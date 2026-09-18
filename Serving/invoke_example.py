#!/usr/bin/env python3
"""
invoke_example.py — correct way to call the sahayak-30b endpoint: CHAT TEMPLATE (messages),
never raw completion. Raw prompts loop; messages work.

    pip install boto3
    AWS_PROFILE=<your-profile> python invoke_example.py
"""
import boto3, json

REGION   = "ap-south-1"
ENDPOINT = "sahayak-30b"

smr = boto3.client("sagemaker-runtime", region_name=REGION)

def ask(user_text, max_tokens=300):
    body = json.dumps({
        "messages": [{"role": "user", "content": user_text}],
        "max_tokens": max_tokens,
        "temperature": 0.0,
        # try to suppress the <think> trace (verify it takes for this model):
        "chat_template_kwargs": {"enable_thinking": False},
    })
    r = smr.invoke_endpoint(EndpointName=ENDPOINT, ContentType="application/json", Body=body)
    out = json.loads(r["Body"].read())
    # LMI chat schema: choices[0].message.content
    return out["choices"][0]["message"]["content"]

if __name__ == "__main__":
    for q in ["What is the capital of France? Answer in one short sentence.",
              "৪০০-এর ১৫% কত? বাংলায় ধাপে ধাপে বোঝাও।"]:
        print("USER:", q)
        print("MODEL:", ask(q), "\n")
