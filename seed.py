from model import db, Event, Calendar, User, UserCal, CalEvent
from datetime import datetime
# from dateutil import relativedelta, parser


def seed_user(profile, user_id):

    first_name = profile['names'][0].get("givenName")
    last_name = profile['names'][0].get("familyName")
    # user_sync_token = calendarsResult['nextSyncToken']
    # calendar_etags = calendarsResult['etag']

    user_exists = User.query.get(user_id)

    # if user_exists:

        # User.user_sync_token = user_sync_token

    if user_exists is None:

        user = User(user_id=user_id,
                    first_name=first_name,
                    last_name=last_name)
                    # user_sync_token=user_sync_token)

        db.session.add(user)
        db.session.commit()

    return user_id


def seed_calendars(calendarsResult, user_id):

    calendars = calendarsResult.get('items', [])

    for calendar in calendars:

        calendar_id = calendar['id'].lower()
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

    return calendar_id


def seed_events(eventsResult):

    for key, value in eventsResult.iteritems():
        items = value.get('items', [])

        for event in items:

            etag = event['etag']
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            creator = event['creator'].get('email', []).lower()
            # status = event['status']
            summary = event['summary'].lower()
            event_id = event['id']

            company = ['hands', 'company', 'office']
            cross_department = ['operations']
            department = ['team']
            vertical = ['standup', 'scrum', 'daily', 'check']
            one_on_one = [':', 'supervisor', 'mentor', 'supervisee', 'manager']
            off_site = ['vendor', 'client', 'investor', 'conference', 'off-site']

            if any(item in summary for item in company):
                label = "company-wide"
            elif any(item in summary for item in cross_department):
                label = "cross-department"
            elif any(item in summary for item in department):
                label = "deparment"
            elif any(item in summary for item in vertical):
                label = "vertical"
            elif any(item in summary for item in one_on_one):
                label = "one-on-one"
            elif any(item in summary for item in off_site):
                label = "off-site"
            else:
                label = None

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
                                  summary=summary,
                                  label=label)

                db.session.add(event_obj)
                db.session.commit()

                calevent = CalEvent(calendar_id=key,
                                    event_id=event_id)

                db.session.add(calevent)
                db.session.commit()
