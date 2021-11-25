import logging
import re
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import mail_managers
from django.http import HttpResponsePermanentRedirect
from django.urls import is_valid_path
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import escape_leading_slashes

logger = logging.getLogger(__name__)


class Http4xxErrorLogMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        """Send broken link emails for relevant 404 NOT FOUND responses."""
        if (
            str(response.status_code)[0] == "4"
            and response.status_code != 401
            and not settings.DEBUG
        ):
            domain = request.get_host()
            path = request.get_full_path()
            referer = request.META.get("HTTP_REFERER", "")

            if not self.is_ignorable_request(
                request, path, domain, referer
            ) and not path.endswith("favicon.ico"):
                ua = request.META.get("HTTP_USER_AGENT", "<none>")
                ip = request.META.get("REMOTE_ADDR", "<none>")
                try:
                    response_data = str(response.data)
                except AttributeError:
                    response_data = "-"

                log_message = (
                    "Error %s on %slink on %s"
                    % (
                        response.status_code,
                        (
                            "INTERNAL "
                            if self.is_internal_request(domain, referer)
                            else ""
                        ),
                        domain,
                    ),
                    "Referrer: %s\nRequested URL: %s\nUser agent: %s\n"
                    "IP address: %s\n"
                    "Requesting user: %s\n"
                    "Response data: %s\n"
                    "Request headers: %s\n"
                    % (
                        referer,
                        path,
                        ua,
                        ip,
                        request.user,
                        response_data,
                        str(request.headers),
                    ),
                )
                logger.warning(log_message)
        return response

    def is_internal_request(self, domain, referer):
        """
        Return True if the referring URL is the same domain as the current
        request.
        """
        # Different subdomains are treated as different domains.
        return bool(re.match("^https?://%s/" % re.escape(domain), referer))

    def is_ignorable_request(self, request, uri, domain, referer):
        """
        Return True if the given request *shouldn't* notify the site managers
        according to project settings or in situations outlined by the inline
        comments.
        """

        # APPEND_SLASH is enabled and the referer is equal to the current URL
        # without a trailing slash indicating an internal redirect.
        if settings.APPEND_SLASH and uri.endswith("/") and referer == uri[:-1]:
            return True

        # A '?' in referer is identified as a search engine source.
        if not self.is_internal_request(domain, referer) and "?" in referer:
            return True

        # The referer is equal to the current URL, ignoring the scheme (assumed
        # to be a poorly implemented bot).
        # parsed_referer = urlparse(referer)
        # if parsed_referer.netloc in ["", domain] and parsed_referer.path == uri:
        #     return True

        return any(pattern.search(uri) for pattern in settings.IGNORABLE_404_URLS)
