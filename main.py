import streamlit as st
import requests
import json
import re
import ast
from io import BytesIO
import urllib.parse
st.title("🧭 Scrape.do Proxy Credit Checker")

def safe_json_loads(text, field_name="Field"):
    """Safely parse input as JSON or Python dict string."""
    if not text.strip():
        return {}
    # Try standard JSON first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try replacing single quotes (JSON fix)
        fixed = re.sub(r"'", '"', text)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            # Try Python literal eval (for dict-style inputs)
            try:
                return ast.literal_eval(text)
            except Exception:
                st.warning(f"⚠️ Invalid format in {field_name}, using empty object.")
                return {}

# --- Proxy Configuration ---
st.subheader("Proxy Configuration")
token = st.text_input("Enter your Scrape.do token", type="password")

st.subheader("Proxy Parameters")
super_mode = st.checkbox("Enable Super Mode", value=True)
custom_headers = st.checkbox("Enable Custom Headers", value=True)
extra_headers = st.checkbox("Enable Extra Headers", value=True)
geo_code = st.text_input("Geo Code (e.g., us, in etc.)", "")

# --- Request Configuration ---
st.subheader("Request Configuration")
url = st.text_input("Request URL (e.g., https://httpbin.org/get)")
method = st.selectbox("HTTP Method", ["GET", "POST"])
headers_text = st.text_area("Headers (JSON or dict format)", "{}", height=120)
# cookies_text = st.text_area("Cookies (JSON or dict format)", "{}", height=80)
params_text = st.text_area("Query Params (JSON or dict format)", "{}", height=80)
json_data_text = st.text_area("JSON Body (JSON or dict format)", "{}", height=120)
timeout_time = st.number_input("Timeout (seconds)", min_value=1, max_value=120, value=30)
if custom_headers and extra_headers:
    st.error("⚠️ You can't use both Custom Headers and Extra Headers at the same time.")
headers = safe_json_loads(headers_text, "Headers")
# cookies = safe_json_loads(cookies_text, "Cookies")
params = safe_json_loads(params_text, "Params")
json_data = safe_json_loads(json_data_text, "JSON Body")

# Build proxy params
proxy_params = []
if geo_code:
    proxy_params.append(f"geoCode={geo_code}")
if super_mode:
    proxy_params.append("super=true")
if extra_headers:
    if headers == {}:
        st.warning("⚠️ Custom Headers enabled but no headers provided.")
    new_headers = {}
    for key in headers.keys():
        new_headers[f'sd-{key}'] = headers[key]
    headers = new_headers
    proxy_params.append("extraHeaders=true")
if custom_headers:
    if headers == {}:
        st.warning("⚠️ Extra Headers enabled but no headers provided.")

    proxy_params.append("customHeaders=true")

proxy_param_str = "&".join(proxy_params)
if method == 'GET':
    if proxy_param_str:
        proxy_url = f"http://{token}:{proxy_param_str}@proxy.scrape.do:8080"
    else:
        proxy_url = f"http://{token}:@proxy.scrape.do:8080"
elif method == 'POST':
    proxy_params = {}
    if proxy_param_str:
        proxy_url = f"http://{token}:{urllib.parse.urlencode(proxy_params)}&{proxy_param_str}@proxy.scrape.do:8080"
    else:
        proxy_url = f"http://{token}:{urllib.parse.urlencode(proxy_params)}@proxy.scrape.do:8080"
proxies = {"http": proxy_url, "https": proxy_url}
if st.button("🔍 Check Proxy Credit"):
    try:


        # Make the request
        with st.spinner("Sending request..."):
            if method == "GET":
                response = requests.get(
                    url,
                    headers=headers,
                    # cookies=cookies,
                    params=params,
                    proxies=proxies,
                    verify=False,
                    timeout=timeout_time,
                )
            else:
                response = requests.post(
                    url,
                    headers=headers,
                    # cookies=cookies,
                    params=params,
                    data=json_data,
                    proxies=proxies,
                    verify=False,
                    timeout=timeout_time,
                )

        # Show results
        cost = response.headers.get("scrape.do-request-cost", "Not Found")
        st.success("✅ Request Completed!")

        st.write(f"**Status Code:** {response.status_code}")
        st.write(f"**Scrape.do Request Cost:** {cost}")
        st.write("---")
        st.write("### Response Preview:")
        st.code(response.text[:1000], language="json")

        # --- Generate Python Script for Download ---
        script_content = f'''import requests

token = "{token}"
proxy_params = "{proxy_param_str}"
proxy_url = f"http://{{token}}:{{proxy_params}}@proxy.scrape.do:8080" if proxy_params else f"http://{{token}}@proxy.scrape.do:8080"
proxies = {{"http": proxy_url, "https": proxy_url}}

url = "{url}"
method = "{method}"
headers = {json.dumps(headers, indent=4)}
params = {json.dumps(params, indent=4)}
json_data = {json.dumps(json_data, indent=4)}

print("🔗 Using Proxy:", proxy_url)

try:
    if method == "GET":
        response = requests.get(url, headers=headers, cookies=cookies, params=params, proxies=proxies, verify=False, timeout=30)
    else:
        response = requests.post(url, headers=headers, cookies=cookies, params=params, json=json_data, proxies=proxies, verify=False, timeout=30)

    print("✅ Status Code:", response.status_code)
    print("💰 Scrape.do Request Cost:", response.headers.get("scrape.do-request-cost", "Not Found"))
    print("📄 Response Preview:\\n", response.text[:500])

except Exception as e:
    print("❌ Error:", e)
'''

        # Prepare file for download
        buffer = BytesIO()
        buffer.write(script_content.encode())
        buffer.seek(0)

        st.download_button(
            label="💾 Download Python Script",
            data=buffer,
            file_name="check_scrapedo_credit.py",
            mime="text/x-python",
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
