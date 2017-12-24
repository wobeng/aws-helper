import json
import time
from datetime import datetime

import botocore.exceptions

from aws_utils.utils import process_exception, datetime_to_unix_time_millis, date_range


class Logs:
    def __init__(self, session):
        self.client = session.client('logs')

    def __call__(self, company, group, subgroup):
        self._log_group_name = '/{}/{}/{}'.format(company, group, subgroup)
        return self

    def get_log(self, start_date=None, end_date=None, log_id=None, log_filter=None):

        flight = dict()

        if start_date and end_date:
            start_date_unix = datetime_to_unix_time_millis(start_date)
            end_date_unix = datetime_to_unix_time_millis(end_date)
            flight['startTime'] = start_date_unix
            flight['endTime'] = end_date_unix

            if log_id:
                log_stream_names = list()
                for date in date_range(start_date, end_date):
                    log_stream_names.append('{}/{}/{}/[$LATEST]{}'.format(date.year, date.month, date.day, log_id))
                flight['logStreamNames'] = log_stream_names

        if log_filter:
            filter_data = '{'
            for k in log_filter:
                cond_and = '&&'
                if filter_data == '{':
                    cond_and = ''
                filter_data += ' {} $.{} = \'{}\''.format(cond_and, k, log_filter[k])
            filter_data += '}'
            flight['filterPattern'] = filter_data

            flight['logGroupName'] = self._log_group_name

        try:
            response = self.client.filter_log_events(**flight)
            return response
        except botocore.exceptions.ClientError as e:
            process_exception(e)
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                raise KeyError()

    def put_log(self, message, log_id):

        while True:

            now = datetime.utcnow()
            log_stream = '{}/{}/{}/[$LATEST]{}'.format(now.year, now.month, now.day, log_id)

            try:
                log_event = {
                    'logGroupName': self._log_group_name,
                    'logStreamName': log_stream,
                    'logEvents': [
                        {
                            'timestamp': int(time.time() * 1000),
                            'message': json.dumps(message)
                        }
                    ]
                }
                response = self.client.describe_log_streams(
                    logGroupName=self._log_group_name,
                    logStreamNamePrefix=log_stream
                )
                if response['logStreams']:
                    if 'uploadSequenceToken' in response['logStreams'][0]:
                        log_event['sequenceToken'] = response['logStreams'][0]['uploadSequenceToken']

                self.client.put_log_events(**log_event)
                break
            except KeyError as e:
                process_exception(e)
                self.client.create_log_stream(logGroupName=self._log_group_name,
                                              logStreamName=log_stream)
            except botocore.exceptions.ClientError as e:
                process_exception(e)
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    if 'log stream' in e.response['Error']['Message']:
                        self.client.create_log_stream(logGroupName=self._log_group_name,
                                                      logStreamName=log_stream)
                    elif 'log group' in e.response['Error']['Message']:
                        self.client.create_log_group(logGroupName=self._log_group_name)
                    else:
                        break
                else:
                    break
