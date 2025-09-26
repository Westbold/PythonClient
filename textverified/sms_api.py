from .action import _ActionPerformer, _Action
from typing import List, Union, Iterator
from .data import (
    Sms,
    Reservation,
    NonrenewableRentalCompact,
    NonrenewableRentalExpanded,
    RenewableRentalCompact,
    RenewableRentalExpanded,
    VerificationCompact,
    VerificationExpanded,
    ReservationType,
    SendSmsRequest,
    ReplySmsRequest,
)
from .paginated_list import PaginatedList
import time
import datetime


class SMSApi:
    """API endpoints related to SMS
    This includes listing SMS messages for rentals and verifications, as well as handling incoming SMS.

    Note that SMS messages are only received by rentals that are awake or always-on.
    """

    def __init__(self, client: _ActionPerformer):
        self.client = client

    def list(
        self,
        data: Union[
            Reservation,
            NonrenewableRentalCompact,
            NonrenewableRentalExpanded,
            RenewableRentalCompact,
            RenewableRentalExpanded,
            VerificationCompact,
            VerificationExpanded,
        ] = None,
        *,
        to_number: str = None,
        reservation_type: ReservationType = None,
    ) -> PaginatedList[Sms]:
        """List SMS messages for rentals and verifications associated with this account.

        You can retrieve all SMS messages across all your rentals and verifications, or filter by specific criteria.
        When providing a rental or verification object, SMS messages for that specific number will be returned.

        Args:
            data (Union[Reservation, NonrenewableRentalCompact, NonrenewableRentalExpanded, RenewableRentalCompact, RenewableRentalExpanded, VerificationCompact, VerificationExpanded], optional): A rental or verification object to get SMS messages for. The phone number will be extracted from this object. Defaults to None.
            to_number (str, optional): Filter SMS messages by the destination phone number. Cannot be used together with data parameter. Defaults to None.
            reservation_type (ReservationType, optional): Filter SMS messages by reservation type (renewable, non-renewable, verification). Cannot be used when providing a data object. Defaults to None.

        Raises:
            ValueError: If both data and to_number are provided, or if reservation_type is specified when using a rental/verification object.

        Returns:
            PaginatedList[Sms]: A paginated list of SMS messages matching the specified criteria.
        """

        # Extract needed data from provided objects
        reservation_id = None
        if data and isinstance(
            data,
            (
                NonrenewableRentalCompact,
                NonrenewableRentalExpanded,
                RenewableRentalCompact,
                RenewableRentalExpanded,
                VerificationCompact,
                VerificationExpanded,
            ),
        ):
            if to_number:
                raise ValueError("Cannot specify both rental/verification data and to_number.")
            to_number = data.number

            if reservation_type is not None:
                raise ValueError("Cannot specify reservation_type when using a rental or verification object.")

        if isinstance(
            data,
            (
                Reservation,
                NonrenewableRentalCompact,
                NonrenewableRentalExpanded,
                RenewableRentalCompact,
                RenewableRentalExpanded,
            ),
        ):
            reservation_id = data.id

        # Construct url params
        params = dict()
        if to_number:
            params["to"] = to_number

        if reservation_id:
            params["reservationId"] = reservation_id

        if isinstance(reservation_type, ReservationType):
            params["reservationType"] = reservation_type.to_api()

        # Construct and perform the action
        action = _Action(method="GET", href="/api/pub/v2/sms")
        response = self.client._perform_action(action, params=params)

        return PaginatedList(request_json=response.data, parse_item=Sms.from_api, api_context=self.client)

    def incoming(
        self,
        data: Union[
            NonrenewableRentalCompact,
            NonrenewableRentalExpanded,
            RenewableRentalCompact,
            RenewableRentalExpanded,
            VerificationCompact,
            VerificationExpanded,
        ] = None,
        *,
        to_number: str = None,
        reservation_type: ReservationType = None,
        timeout: float = 10.0,
        polling_interval: float = 1.0,
        wake_number: bool = False,
        since: datetime.datetime = None,
    ) -> Iterator[Sms]:
        """Wait for and yield incoming SMS messages in real-time.

        This method polls for new SMS messages and yields them as they arrive. It will wait up to the specified timeout
        for new messages. The polling stops after the first batch of new messages is received or the timeout is reached.

        Note: Only rentals that are awake or always-on can receive SMS messages. Use wake_number=True to automatically
        wake a rental before polling for messages.

        Args:
            data (Union[NonrenewableRentalCompact, NonrenewableRentalExpanded, RenewableRentalCompact, RenewableRentalExpanded, VerificationCompact, VerificationExpanded], optional): A rental or verification object to monitor for incoming SMS. Defaults to None.
            to_number (str, optional): Filter incoming SMS by destination phone number. Cannot be used together with data parameter. Defaults to None.
            reservation_type (ReservationType, optional): Filter incoming SMS by reservation type. Cannot be used when providing a data object. Defaults to None.
            timeout (float, optional): Maximum time in seconds to wait for incoming messages. If negative, no timeout will be applied. Defaults to 10.0.
            polling_interval (float, optional): Time in seconds between polling attempts. Defaults to 1.0.
            wake_number (bool, optional): Whether to automatically wake the rental before polling. Only works with rental objects, not verifications. Defaults to False.
            since (datetime.datetime, optional): Only yield messages created after this timestamp. Defaults to datetime.datetime.now().
        Raises:
            ValueError: If wake_number is True but no rental data is provided, or if attempting to wake a verification.

        Yields:
            Sms: New SMS messages as they arrive.
        """

        if wake_number:
            if data and isinstance(
                data,
                (
                    NonrenewableRentalCompact,
                    NonrenewableRentalExpanded,
                    RenewableRentalCompact,
                    RenewableRentalExpanded,
                ),
            ):
                self.client.wake_requests.wait_for_number_wake(data)  # suspicious in terms of typing
            elif data and isinstance(data, (VerificationCompact, VerificationExpanded)):
                raise ValueError("Cannot wake a verification.")
            else:
                raise ValueError("Must provide reservation data to auto-wake wake the number.")

        if timeout < 0:
            timeout = float("inf")

        if since is None:
            since = datetime.datetime.now(datetime.timezone.utc)
        if not isinstance(since, datetime.datetime):
            raise ValueError("since must be a datetime object.")

        earliest_msg = since - datetime.timedelta(seconds=polling_interval)  # allow some leniency
        start_time = time.monotonic()

        already_seen = set()

        # wait up to [timeout] seconds for a NEW message
        while time.monotonic() - start_time < timeout:
            time.sleep(polling_interval)  # Polling interval
            all_messages = self.list(data=data, to_number=to_number, reservation_type=reservation_type)
            unseen_messages = list(
                filter(lambda msg: msg.id not in already_seen and msg.created_at > earliest_msg, all_messages)
            )  # TODO: collapsing this iterator costs a few extra api requests, optimize if possible
            if unseen_messages:
                for msg in unseen_messages:
                    already_seen.add(msg.id)
                    yield msg
                return  # Exit after first batch of unseen messages

    def send(
        self,
        data: SendSmsRequest = None,
        *,
        reservation_id: Union[
            str, RenewableRentalCompact, RenewableRentalExpanded, NonrenewableRentalCompact, NonrenewableRentalExpanded
        ] = None,
        send_to: str = None,
        content: str = None,
    ) -> bool:
        """Send an SMS message from a renewable reservation.

        This method allows you to send an SMS message from one of your renewable rental numbers to any destination phone number.
        The rental must be active and have SMS capability enabled.

        Args:
            data (SendSmsRequest, optional): The SMS sending details. All kwargs will overwrite values in this object. Defaults to None.
            reservation_id (Union[str, RenewableRentalCompact, RenewableRentalExpanded], optional): The ID or instance of the renewable reservation to send from. Defaults to None.
            send_to (str, optional): The destination phone number in the format 1112223333 (digits only). Defaults to None.
            content (str, optional): The message content to send. Defaults to None.

        Raises:
            ValueError: If reservation_id is not valid, send_to is not a valid phone number, or content is empty.

        Returns:
            bool: True if the SMS was sent successfully, False otherwise.
        """
        if reservation_id and isinstance(
            reservation_id,
            (RenewableRentalCompact, RenewableRentalExpanded, NonrenewableRentalCompact, NonrenewableRentalExpanded),
        ):
            reservation_id = reservation_id.id

        data = SendSmsRequest(
            reservation_id=reservation_id or (data.reservation_id if data else None),
            send_to=send_to or (data.send_to if data else None),
            content=content or (data.content if data else None),
        )

        if not isinstance(data.reservation_id, str) or not data.reservation_id.strip():
            raise ValueError(
                "reservation_id must be a valid ID or instance of RenewableRentalCompact/RenewableRentalExpanded."
            )

        if not isinstance(data.send_to, str) or not data.send_to.strip() or not data.send_to.isdigit():
            raise ValueError("send_to must be a valid phone number in the form of 1112223333.")

        if not data.content:
            raise ValueError("content is required to send a message.")

        action = _Action(method="POST", href="/api/pub/v2/sms/reply")
        self.client._perform_action(action, json=data.to_api())

        return True

    def reply(
        self, data: ReplySmsRequest = None, *, reply_to_sms_id: Union[str, Sms] = None, content: str = None
    ) -> bool:
        """Reply to an incoming SMS message.

        This method allows you to reply to a specific SMS message that was received on one of your rentals.
        The reply will be sent from the same number that received the original message.

        Args:
            data (ReplySmsRequest, optional): The SMS reply details. All kwargs will overwrite values in this object. Defaults to None.
            reply_to_sms_id (Union[str, Sms], optional): The ID or instance of the SMS message to reply to. Defaults to None.
            content (str, optional): The reply message content to send. Defaults to None.

        Raises:
            ValueError: If reply_to_sms_id is not valid or content is empty.

        Returns:
            bool: True if the reply was sent successfully, False otherwise.
        """
        # Extract SMS ID from object if provided
        if reply_to_sms_id and isinstance(reply_to_sms_id, Sms):
            reply_to_sms_id = reply_to_sms_id.id

        data = ReplySmsRequest(
            reply_to_sms_id=reply_to_sms_id or (data.reply_to_sms_id if data else None),
            content=content or (data.content if data else None),
        )

        if not isinstance(data.reply_to_sms_id, str) or not data.reply_to_sms_id.strip():
            raise ValueError("reply_to_sms_id must be a valid ID or instance of Sms.")

        if not data.content:
            raise ValueError("content is required to send a reply.")

        action = _Action(method="POST", href="/api/pub/v2/sms/send")
        self.client._perform_action(action, json=data.to_api())

        return True
