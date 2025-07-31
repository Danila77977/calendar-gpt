from __future__ import print_function
import os, datetime, argparse
from dateutil import parser as date_parser
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Зона по умолчанию (московское время UTC+3)
TIMEZONE_OFFSET = '+03:00'

# Области доступа: полный доступ к календарю
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]

def get_credentials():
    """Авторизация и получение credentials."""
    if os.path.exists('token.json'):
        return Credentials.from_authorized_user_file('token.json', SCOPES)
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as f:
        f.write(creds.to_json())
    return creds


def get_free_slots(date_str, start_hour=9, end_hour=18, slot_min=30):
    """
    Показать свободные слоты на указанную дату.
    date_str: строка 'YYYY-MM-DD'
    start_hour, end_hour: границы рабочего дня
    slot_min: длительность слота в минутах
    """
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    day = datetime.datetime.fromisoformat(date_str)
    tmin = day.replace(hour=start_hour, minute=0).isoformat() + TIMEZONE_OFFSET
    tmax = day.replace(hour=end_hour, minute=0).isoformat() + TIMEZONE_OFFSET

    fb = service.freebusy().query(
        body={
            'timeMin': tmin,
            'timeMax': tmax,
            'items': [{'id': 'primary'}]
        }
    ).execute()
    busy_times = fb['calendars']['primary']['busy']
    busy = [(date_parser.isoparse(slot['start']), date_parser.isoparse(slot['end'])) for slot in busy_times]

    slots = []
    pointer = date_parser.isoparse(tmin)
    delta = datetime.timedelta(minutes=slot_min)
    end_pointer = date_parser.isoparse(tmax)

    while pointer + delta <= end_pointer:
        if not any(not (pointer + delta <= b_start or pointer >= b_end) for b_start, b_end in busy):
            slots.append((pointer, pointer + delta))
        pointer += delta

    if slots:
        print('Свободные слоты:')
        for start, end in slots:
            print(f"- {start.strftime('%Y-%m-%d %H:%M')} — {end.strftime('%H:%M')}")
    else:
        print('Нет свободных слотов.')
    return slots


def create_event(start_iso, end_iso, email):
    """
    Создать событие с Google Meet.
    start_iso, end_iso: строки ISO с часовым поясом '+03:00', например '2025-08-01T14:00:00+03:00'
    email: адрес приглашённого
    """
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    event = {
        'summary': 'Встреча с лидом',
        'start': {'dateTime': start_iso},
        'end':   {'dateTime': end_iso},
        'attendees': [{'email': email}],
        'conferenceData': {'createRequest': {'requestId': 'meet-' + start_iso}}
    }

    created = service.events().insert(
        calendarId='primary',
        body=event,
        conferenceDataVersion=1,
        sendUpdates='all'
    ).execute()
    print('Ссылка на встречу:', created.get('hangoutLink'))
    return created


def main():
    parser = argparse.ArgumentParser(prog='calendar_bot.py')
    subparsers = parser.add_subparsers(dest='cmd')

    # Команда для получения слотов
    p1 = subparsers.add_parser('get_slots', help='Показать свободные слоты')
    p1.add_argument('--date', required=True, help='Дата в формате YYYY-MM-DD')

    # Команда для создания встречи
    p2 = subparsers.add_parser('create_event', help='Создать встречу')
    p2.add_argument('--start', required=True, help='Начало события ISO, пример: 2025-08-01T14:00:00+03:00')
    p2.add_argument('--end',   required=True, help='Окончание события ISO, пример: 2025-08-01T14:30:00+03:00')
    p2.add_argument('--email', required=True, help='Email участника встречи')

    args = parser.parse_args()
    if args.cmd == 'get_slots':
        get_free_slots(args.date)
    elif args.cmd == 'create_event':
        create_event(args.start, args.end, args.email)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
