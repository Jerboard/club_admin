from django.shortcuts import render
from django.http import HttpRequest, JsonResponse

import json

from club_bot import bot
from club_bot.models import PaymentPS, User, PhotosTable
from club_bot.utils import add_months
from club_bot.enums import RecurrentStatus
from club_bot.bot.base import log_error


# принимает инфу в апи
def simple_payment(request: HttpRequest):
    response = {'info': 'bad request'}

    text = f'simple_payment\n\nheader===\n{request.headers}\n\nbody===\n{request.body}'
    bot.send_message_admin(text)
    log_error (message=request.body, with_traceback=False)
    bot.send_message_admin ('Прошёл лог')
    try:
        request_data = json.loads(request.body)
        log_error(request.headers, with_traceback=False)
        log_error(request_data, with_traceback=False)
        # for k, v in request_data.items():
        #     print(f'{k}: {v}')
        #     простая оплата
        if request_data['Event'] == "Payment":
            user_id, add_mounts_count, tariff, chat_id, message_id = map(int, request_data['Description'].split(':'))
            order_id = request_data['OrderId']

            payment = PaymentPS.objects.filter (order_id=order_id).first ()

            payment.status = 'success'
            payment.transaction_id = request_data['TransactionId']
            payment.save()

            user_info = User.objects.filter (user_id=user_id).first ()

            new_kick_date = add_months(count_mounts=add_mounts_count, kick_date=user_info.kick_date)
            user_status = user_info.status
            user_info.kick_date = new_kick_date
            user_info.tariff = tariff
            user_info.status = 'sub'
            user_info.recurrent = False
            user_info.save()

            # photo = PhotosTable.objects.order_by("?").first()

            bot.success_payment(
                user_id=user_id,
                message_id=message_id,
                new_kick_date=new_kick_date,
                user_status=user_status
            )

        response = {'info': 'successfully'}

    except Exception as ex:
        log_error(ex)

    finally:
        return JsonResponse(response)


# обычная оплата без реккурента
'''
 "Event": "Payment",
  "Amount": "10.00",
  "Currency": "RUB",
  "DateTime": "03.04.2024 18.43.22",
  "IsTest": 0,
  "Email": "dgushch@gmail.com",
  "Brand": "MASTERCARD",
  "Bank": "SBERBANK OF RUSSIA",
  "Country_Code_Alpha2": "RU",
  "TransactionId": "PS00000412248874",
  "OrderId": "5772948261-7500-4",
  "Description": "5772948261",
  "CustomFields": "pay_type=ontime;WebhookUrl=https%3A//webhook.site/c32e0033-ee49-40cc-a5ce-18afb610b832;original_service_id=22029;ScreenHeight=864;ScreenWidth=1536;JavaEnabled=False;TimeZoneOffset=-240;Region=ru-RU;ColorDepth=24;UserAgent=Mozilla/5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit/537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome/123.0.0.0%20Safari/537.36;acceptHeader=text/html;javaScriptEnabled=True;Email=dgushch%40gmail.com;IP=212.58.120.107;ReceiptEmail=dgushch%40gmail.com;IsSendReceipt=True",
  "Service_Id": "22029",
  "PaymentMethod": "Card",
  "CardMasked": "533669******3348",
  "ExpirationDate": "05/22",
  "RRN": "024773672255",
  "CardHolder": "User Userovich",
  "RebillId": "PS00000412248874"
'''


def recurrent_payment(request: HttpRequest):
    text = f'recurrent_payment\n\nheader===\n{request.headers}\n\nbody===\n{request.body}'
    bot.send_message_admin (text)
    log_error(message=request.body, with_traceback=False)
    request_data = json.loads(request.body)
    user_id = int(request_data['AccountId'])
    if request_data['RecurringStatus'] == RecurrentStatus.NEW.value:
        user_info = User.objects.filter (user_id=user_id).first ()
        user_info.recurrent = True
        user_info.save ()

    elif request_data['RecurringStatus'] == RecurrentStatus.ACTIVE.value:
        pass

    elif request_data['RecurringStatus'] == RecurrentStatus.OVERDUE.value:
        pass

    elif request_data['RecurringStatus'] == RecurrentStatus.TERMINATED.value:
        pass

    else:
        return JsonResponse({'info': 'bad request'})


# удачная оплата с подключением реккурента
'''
{
  "RebillId": "PS00000412176545",
  "Amount": "10.00",
  "Currency": "RUB",
  "Description": "5772948261",
  "WebhookUrl": "https://webhook.site/c32e0033-ee49-40cc-a5ce-18afb610b832",
  "AccountId": "5772948261",
  "Email": "dgushch@gmail.com",
  "Interval": "1",
  "Period": "month",
  "MaxPeriods": "999",
  "RecurringId": "330150",
  "ReceiptData": {},
  "Event": "RegisterRecurring",
  "RecurringStatus": "new",
  "StartDate": "2024-05-03T14:02+0000"
}
'''

# удачная снятие реккурента
'''
{
  "RebillId": "PS00000411124013",
  "Amount": "15.00",
  "Currency": "RUB",
  "Description": "tg_user_id",
  "WebhookUrl": "https://webhook.site/c32e0033-ee49-40cc-a5ce-18afb610b832",
  "AccountId": "order63",
  "Interval": "1",
  "Period": "day",
  "MaxPeriods": "15",
  "RecurringId": "329183",
  "Recurrent": {
    "TransactionId": "PS00000412161345",
    "TransactionState": "success"
  },
  "Event": "ChangeRecurringState",
  "RecurringStatus": "active",
  "StartDate": "2024-04-03T13:42+0000",
  "LatestPay": "2024-04-03T13:42+0000"
}
'''
# неудачное снятие реккурента
'''
{
  "RebillId": "PS00000411124013",
  "Amount": "15.00",
  "Currency": "RUB",
  "Description": "tg_user_id",
  "WebhookUrl": "https://webhook.site/c32e0033-ee49-40cc-a5ce-18afb610b832",
  "AccountId": "order63",
  "Interval": "1",
  "Period": "day",
  "MaxPeriods": "15",
  "RecurringId": "329183",
  "Recurrent": {
    "TransactionId": "PS00000413369679",
    "TransactionState": "declined",
    "TransactionStateDetails": {
      "Code": "",
      "Description": ""
    }
  },
  "Event": "ChangeRecurringState",
  "RecurringStatus": "overdue",
  "StartDate": "2024-04-03T13:42+0000",
  "LatestPay": "2024-04-03T13:42+0000"
}
'''

# отмена реккурена
'''
{
  "RebillId": "PS00000411124013",
  "Amount": "15.00",
  "Currency": "RUB",
  "Description": "tg_user_id",
  "WebhookUrl": "https://webhook.site/c32e0033-ee49-40cc-a5ce-18afb610b832",
  "AccountId": "order63",
  "Interval": "1",
  "Period": "day",
  "MaxPeriods": "15",
  "RecurringId": "329183",
  "Recurrent": {
    "TransactionId": "PS00000415548067",
    "TransactionState": "declined",
    "TransactionStateDetails": {
      "Code": "",
      "Description": ""
    }
  },
  "Event": "ChangeRecurringState",
  "RecurringStatus": "terminated",
  "StartDate": "2024-04-03T13:42+0000",
  "LatestPay": "2024-04-03T13:42+0000"
}
'''
