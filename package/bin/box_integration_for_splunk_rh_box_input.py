import import_declare_test

from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    DataInputModel,
)
from splunktaucclib.rest_handler import admin_external, util
from box_integration_for_splunk_rh_validate_input import BoxInpuHandler
import logging

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        "input_name",
        required=False,
        encrypted=False,
        default=None,
        validator=validator.AllOf(
            validator.Pattern(
                regex=r"""^[a-zA-Z]\w*$""",
            ),
            validator.String(
                max_len=100,
                min_len=1,
            ),
        ),
    ),
    field.RestField(
        "account", required=True, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "rest_endpoint", required=True, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "collect_folder", required=False, encrypted=False, default=1, validator=None
    ),
    field.RestField(
        "collect_collaboration",
        required=False,
        encrypted=False,
        default=1,
        validator=None,
    ),
    field.RestField(
        "collect_file", required=False, encrypted=False, default=1, validator=None
    ),
    field.RestField(
        "collect_task", required=False, encrypted=False, default=1, validator=None
    ),
    field.RestField(
        "created_after", required=False, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "event_delay",
        required=False,
        encrypted=False,
        default=0,
        validator=validator.Pattern(
            regex=r"""^[1-9]\d*$|^\d*$""",
        ),
    ),
    field.RestField(
        "interval",
        required=True,
        encrypted=False,
        default=60,
        validator=validator.AllOf(
            validator.Number(
                max_val=31536000,
                min_val=1,
            ),
            validator.Pattern(
                regex=r"""^\d+$""",
            ),
        ),
    ),
    field.RestField(
        "duration",
        required=False,
        encrypted=False,
        default=60,
        validator=validator.AllOf(
            validator.Number(
                max_val=31536000,
                min_val=1,
            ),
            validator.Pattern(
                regex=r"""^\d+$""",
            ),
        ),
    ),
    field.RestField(
        "index",
        required=True,
        encrypted=False,
        default="default",
        validator=validator.String(
            max_len=80,
            min_len=1,
        ),
    ),
    field.RestField("disabled", required=False, validator=None),
]
model = RestModel(fields, name=None)


endpoint = DataInputModel(
    "box_input",
    model,
)


if __name__ == "__main__":
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=BoxInpuHandler,
    )
