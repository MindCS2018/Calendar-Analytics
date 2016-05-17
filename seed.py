from model import db, Event, Calendar, User, UserCal, CalEvent
import datetime


def seed_db(service):

    user_id = "1"

    calendarsResult = service.calendarList().list().execute()

    # next_sync_token = calendarsResult['nextSyncToken']
    # calendar_etags = calendarsResult['etag']

    user_exists = User.query.get(user_id)

    if user_exists is None:

        user = User(user_id=user_id)
                    # username=username,
                    # user_email=user_email)

        db.session.add(user)
        db.session.commit()

    calendars = calendarsResult.get('items', [])

    id_list = []

    for calendar in calendars:

        calendar_id = calendar['id']
        timezone = calendar['timeZone']
        summary = calendar['summary']
        etag = calendar['etag']

        if 'primary' in calendar:
            primary = calendar['primary']
            # user_id = calendar_id
        else:
            primary = False

        if 'selected' in calendar:
            selected = calendar['selected']
            id_list.append(calendar_id)
        else:
            selected = False

        # if calendar_exists and calendar_exists.etag == etag:
        # else:

        cal_exists = Calendar.query.get(calendar_id)
        usercal_exists = UserCal.query.filter_by(user_id=user_id,
                                                 calendar_id=calendar_id).first()

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

            db.session.add(calendar_obj)
            db.session.commit()

            usercal = UserCal(user_id=user_id,
                              calendar_id=calendar_id,
                              primary=primary,
                              selected=selected)

            db.session.add(usercal)
            db.session.commit()

    # 'Z' indicates UTC time
    now = datetime.datetime.utcnow().isoformat() + 'Z'

    for id_ in id_list:  # for each calendar

        eventsResult = service.events().list(calendarId=id_,
                                             timeMin=now,
                                             maxResults=100,
                                             singleEvents=True,
                                             orderBy='startTime').execute()

        # events_etag = eventsResult['etag']
        # events_email = eventsResult['summary']
        # events_timezone = eventsResult['timeZone']
        # events_updated_at = eventsResult['updated']

        events = eventsResult.get('items', [])  # pulls events

        for event in events:

            etag = event['etag']

            # datetime objects
            start = event['start'].get('dateTime', event['start'].get('date'))

            if 'dateTime' in event['start']:
                start_time = start[11:]
            else:
                start_time = "00:00:00"

            # datetime objects
            end = event['end'].get('dateTime', event['start'].get('date'))

            creator = event['creator'].get('email', [])
            # status = event['status']
            summary = event['summary']
            event_id = event['id']
            created_at = event['created']
            updated_at = event['updated']

            # if event is not already in database:
                # add event
                # add guest
            # else: (if event is in the database)
                # if we haven't looked @ their calendar before
                # add guest

            # if 'attendees' in event:
            #     attendees = event['attendees']
            # else:
            #     conf_rm = None

            # for attendee in attendees:
            #     if 'resource' in attendee:
            #         conf_rm = attendee['displayName']
            #         break
            #     else:
            #         conf_rm = None

            # event_exists in db
            event_exists = Event.query.get(event_id)
            calevents_exists = CalEvent.query.filter_by(calendar_id=id_,
                                                        event_id=event_id).first()

            if event_exists and calevents_exists is None:

                calevent = CalEvent(calendar_id=id_,
                                    event_id=event_id)

                db.session.add(calevent)
                db.session.commit()

            # elif event_exists and event_exists.etag != etag:

            #     event_exists.etag = etag
            #     event_exists.creator = creator
            #     event_exists.start = start
            #     event_exists.end = end
            #     event_exists.created_at = created_at
            #     event_exists.updated_at = updated_at
            #     event_exists.summary = summary

            #     calevent = CalEvent(calendar_id=id_,
            #                         event_id=event_id,
            #                         status=status)

            #     db.session.add(calevent)
            #     db.session.commit()

            elif event_exists is None:

            # if 'attendees' in event:
            #     attendees = event['attendees']
            #     print(attendees)

            #     for attendee in attendees:
            #         if 'resource' in attendee:
            #             display_name = attendee['displayName']
            #             print(display_name)
            #         else:
            #             email = attendee['email']
            #             print(email)

                event_obj = Event(event_id=event_id,
                                  etag=etag,
                                  creator=creator,
                                  start=start,
                                  start_time=start_time,
                                  end=end,
                                  created_at=created_at,
                                  updated_at=updated_at,
                                  summary=summary)

                db.session.add(event_obj)
                db.session.commit()

                calevent = CalEvent(calendar_id=id_,
                                    event_id=event_id)

                db.session.add(calevent)
                db.session.commit()
