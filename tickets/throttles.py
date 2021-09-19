from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AnonTicketSubmissionThrottle(AnonRateThrottle):
    scope = "burst"
    rate = "1/hour"
    # def parse_rate(self, rate):
    #     """
    #     returns a tuple:  <allowed number of requests>, <period of time in seconds>
    #     which is fixed to allow 1 request every 30 seconds
    #     """
    #     return (1, 60 * 60)  # one request per hour


class UserTicketSubmissionThrottle(UserRateThrottle):
    scope = "burst"
    rate = "1/hour"


#     def parse_rate(self, rate):
#         """
#         returns a tuple:  <allowed number of requests>, <period of time in seconds>
#         which is fixed to allow 1 request every 30 seconds
#         """
#         return (1, 60 * 60)  # one request per hour
