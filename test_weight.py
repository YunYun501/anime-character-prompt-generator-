import sys
sys.path.insert(0, '.')

from web.routes.prompt import build_prompt_string
from web.routes.prompt import GenerateRequest, SlotState

slots = {
    'upper_body': SlotState(
        enabled=True,
        value_id='shirt',
        value='shirt',
        color='blue',
        weight=1.5
    )
}

req = GenerateRequest(
    slots=slots,
    full_body_mode=False,
    upper_body_mode=False,
    output_language='en'
)

result = build_prompt_string(req)
print('Result:', repr(result))
print('Contains :1.5?', ':1.5' in result)
print('Contains (blue shirt:1.5)?', '(blue shirt:1.5)' in result)