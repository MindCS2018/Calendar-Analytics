from model import db, Event, Calendar, User, UserCal, CalEvent
from datetime import datetime
# from dateutil import relativedelta, parser


def seed_db(profile, calendarsResult, eventsResult):

    user_id = profile['names'][0]['metadata']['source']['id']
    first_name = profile['names'][0].get("givenName")
    last_name = profile['names'][0].get("familyName")
    full_name = profile['names'][0].get("displayName")
    # user_sync_token = calendarsResult['nextSyncToken']
    # calendar_etags = calendarsResult['etag']

    user_exists = User.query.get(user_id)

    # if user_exists:

        # User.user_sync_token = user_sync_token

    if user_exists is None:

        user = User(user_id=user_id,
                    first_name=first_name,
                    last_name=last_name,
                    full_name=full_name)
                    # user_sync_token=user_sync_token)

        db.session.add(user)
        db.session.commit()

    calendars = calendarsResult.get('items', [])

    print("for loop before calendars")
    print datetime.now()
    print("\n")

    for calendar in calendars:

        calendar_id = calendar['id']
        timezone = calendar['timeZone']
        summary = calendar['summary']
        etag = calendar['etag']

        if 'primary' in calendar:
            primary = calendar['primary']

        else:
            primary = False

        if 'selected' in calendar:
            selected = calendar['selected']

        else:
            selected = False

        # if calendar_exists and calendar_exists.etag == etag:
        # else:

        cal_exists = Calendar.query.get(calendar_id)
        usercal_exists = UserCal.query.filter_by(user_id=user_id,
                                                 calendar_id=calendar_id).first()

        # if next page token exists, call back to the api with the next page token
        # next sync token @ the end
        # calendar_sync_token = eventsResult[calendar_id]['nextSyncToken']

        if cal_exists and usercal_exists is None:

            usercal = UserCal(user_id=user_id,
                              calendar_id=calendar_id,
                              primary=primary,
                              selected=selected)

            # usercal.calendar_id = calendar_id

            db.session.add(usercal)
            db.session.commit()

        # elif cal_exists and cal_exists.etag != etag:
        #     update db

        elif cal_exists is None:

            calendar_obj = Calendar(calendar_id=calendar_id,
                                    etag=etag,
                                    summary=summary,
                                    timezone=timezone)
                                    # calendar_sync_token=calendar_sync_token)

            db.session.add(calendar_obj)
            db.session.commit()

            usercal = UserCal(user_id=user_id,
                              calendar_id=calendar_id,
                              primary=primary,
                              selected=selected)

            db.session.add(usercal)
            db.session.commit()

    print("finished calendar for loop")
    print datetime.now()
    print("\n")

    for key, value in eventsResult.iteritems():
        items = value.get('items', [])

        print("before event assigning")
        print datetime.now()
        print("\n")

        for event in items:

            etag = event['etag']
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['start'].get('date'))
            creator = event['creator'].get('email', [])
            # status = event['status']
            summary = event['summary']
            event_id = event['id']

            event_exists = Event.query.get(event_id)
            calevents_exists = CalEvent.query.filter_by(calendar_id=key,
                                                        event_id=event_id).first()

            if event_exists and calevents_exists is None:

                calevent = CalEvent(calendar_id=key,
                                    event_id=event_id)

                db.session.add(calevent)
                db.session.commit()

            elif event_exists is None:

                event_obj = Event(event_id=event_id,
                                  etag=etag,
                                  creator=creator,
                                  start=start,
                                  end=end,
                                  summary=summary)

                db.session.add(event_obj)
                db.session.commit()

                calevent = CalEvent(calendar_id=key,
                                    event_id=event_id)

                db.session.add(calevent)
                db.session.commit()

        print("after event assigning")
        print datetime.now()
        print("\n")
