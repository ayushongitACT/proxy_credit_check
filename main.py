import streamlit as st
import requests
import json
import re
import ast
from io import BytesIO

st.title("🧭 Universal Proxy Credit Checker")

def safe_json_loads(text, field_name="Field"):
    """Safely parse input as JSON or Python dict string."""
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fixed = re.sub(r"'", '"', text)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(text)
            except Exception:
                st.warning(f"⚠️ Invalid format in {field_name}, using empty object.")
                return {}

# --- Platform Selection ---
st.subheader("Proxy Provider")
platform = st.selectbox(
    "Select Proxy Provider",
    ["Scrape.do", "ScraperAPI", "Custom Proxy"]
)

# --- Proxy Configuration ---
token = ""
api_key = ""
proxies = {}
proxy_params = []

if platform == "Scrape.do":
    st.subheader("Scrape.do Configuration")
    token = st.text_input("Enter your Scrape.do token")

    st.subheader("Proxy Parameters")
    super_mode = st.checkbox("Enable Super Mode", value=True)
    custom_headers = st.checkbox("Enable Custom Headers", value=True)
    extra_headers = st.checkbox("Enable Extra Headers", value=True)
    geo_code = st.text_input("Geo Code (e.g., us, in etc.)", "")

elif platform == "ScraperAPI":
    st.subheader("ScraperAPI Configuration")
    api_key = st.text_input("Enter your ScraperAPI key")
    geo_code = st.text_input("Country Code (e.g., us, in etc.)", "")
    render = st.checkbox("Enable Render Mode", value=False)
    premium = st.checkbox("Use Premium Proxy", value=False)
    ultra_premium = st.checkbox("Use Ultra Premium Proxy", value=False)
    autoparse = st.checkbox("Enable Auto Parse", value=False)
    keep_headers = st.checkbox("Keep Headers", value=True)
    device_type = st.selectbox("Device Type", ["desktop", "mobile"], index=0)

elif platform == "Custom Proxy":
    st.subheader("Custom Proxy Configuration")
    proxy_type = st.selectbox("Proxy Input Type", ["Proxy URL", "Proxy Dictionary"])
    if proxy_type == "Proxy URL":
        custom_proxy_url = st.text_input("Enter Proxy URL (e.g., http://user:pass@ip:port)")
    else:
        custom_proxy_dict_text = st.text_area("Proxy Dict (JSON or dict format)", "{}", height=120)

# --- Request Configuration ---
st.subheader("Request Configuration")
url = st.text_input("Request URL (e.g., https://httpbin.org/get)")
method = st.selectbox("HTTP Method", ["GET", "POST"])
headers_text = st.text_area("Headers (JSON or dict format)", "{}", height=120)
cookies_text = st.text_area("Cookies (JSON or dict format)", "{}", height=80)
params_text = st.text_area("Query Params (JSON or dict format)", "{}", height=80)
json_data_text = st.text_area("JSON Body (JSON or dict format)", "{}", height=120)

if st.button("🔍 Check Proxy Credit"):
    try:
        headers = safe_json_loads(headers_text, "Headers")
        cookies = safe_json_loads(cookies_text, "Cookies")
        params = safe_json_loads(params_text, "Params")
        json_data = safe_json_loads(json_data_text, "JSON Body")

        response = None
        cost = "Not Available"

        # --- SCRAPE.DO ---
        if platform == "Scrape.do":
            proxy_params = []
            if geo_code:
                proxy_params.append(f"geoCode={geo_code}")
            if super_mode:
                proxy_params.append("super=true")
            if custom_headers:
                proxy_params.append("customHeaders=true")
            if extra_headers:
                proxy_params.append("extraHeaders=true")

            proxy_param_str = "&".join(proxy_params)
            proxy_url = f"http://{token}:{proxy_param_str}@proxy.scrape.do:8080" if proxy_param_str else f"http://{token}:@proxy.scrape.do:8080"
            proxies = {"http": proxy_url, "https": proxy_url}

            with st.spinner("Sending request via Scrape.do..."):
                if method == "GET":
                    response = requests.get(url, headers=headers, cookies=cookies, params=params, proxies=proxies, verify=False, timeout=30)
                else:
                    response = requests.post(url, headers=headers, cookies=cookies, params=params, json=json_data, proxies=proxies, verify=False, timeout=30)

            cost = response.headers.get("scrape.do-request-cost", "Not Found")

        # --- SCRAPERAPI ---
        elif platform == "ScraperAPI":
            # Construct ScraperAPI URL for actual site request
            scraperapi_url = f"https://api.scraperapi.com/?api_key={api_key}&url={url}"
            extra_params = {
                "render": str(render).lower(),
                "country_code": geo_code,
                "premium": str(premium).lower(),
                "ultra_premium": str(ultra_premium).lower(),
                "autoparse": str(autoparse).lower(),
                "keep_headers": str(keep_headers).lower(),
                "device_type": device_type
            }
            extra_params = {k: v for k, v in extra_params.items() if v and v not in ["false", ""]}

            with st.spinner("Sending request via ScraperAPI (fetching actual site)..."):
                if method == "GET":
                    response = requests.get(scraperapi_url, headers=headers, cookies=cookies, params={**params, **extra_params}, timeout=30)
                else:
                    response = requests.post(scraperapi_url, headers=headers, cookies=cookies, params={**params, **extra_params}, json=json_data, timeout=30)

            # Fetch credit cost info separately
            base_endpoint = "https://api.scraperapi.com/account/urlcost"
            credit_params = {"api_key": api_key, "url": url, "render": str(render).lower()}
            credit_resp = requests.get(base_endpoint, params=credit_params, timeout=30)
            try:
                data = credit_resp.json()
                cost = data.get("credits", "Not Found")
            except Exception:
                cost = "Invalid Response"

        # --- CUSTOM PROXY ---
        elif platform == "Custom Proxy":
            if proxy_type == "Proxy URL":
                proxies = {"http": custom_proxy_url, "https": custom_proxy_url}
            else:
                proxies = safe_json_loads(custom_proxy_dict_text, "Proxy Dict")

            with st.spinner("Sending request via Custom Proxy..."):
                if method == "GET":
                    response = requests.get(url, headers=headers, cookies=cookies, params=params, proxies=proxies, verify=False, timeout=30)
                else:
                    response = requests.post(url, headers=headers, cookies=cookies, params=params, json=json_data, proxies=proxies, verify=False, timeout=30)

        # --- Display Results ---
        st.success("✅ Request Completed!")
        st.write(f"**Status Code:** {response.status_code if response else 'N/A'}")
        st.write(f"**Proxy Credit / Cost:** {cost}")
        st.write("---")
        st.write("### Response Preview (Original Site Response):")
        if response is not None:
            preview_text = response.text[:1000]
            st.code(preview_text, language="json" if preview_text.strip().startswith("{") else "html")
        else:
            st.info("No response to display.")

        # --- Generate Python Script ---
        if platform == "Scrape.do":
            script_content = f'''import requests

token = "{token}"
proxy_params = "{'&'.join(proxy_params)}"
proxy_url = f"http://{{token}}:{{proxy_params}}@proxy.scrape.do:8080" if proxy_params else f"http://{{token}}@proxy.scrape.do:8080"
proxies = {{"http": proxy_url, "https": proxy_url}}

url = "{url}"
response = requests.get(url, proxies=proxies, verify=False)
print("Status:", response.status_code)
print("Scrape.do Request Cost:", response.headers.get("scrape.do-request-cost", "Not Found"))
print(response.text[:500])
'''

        elif platform == "ScraperAPI":
            script_content = f'''import requests

api_key = "{api_key}"
url = "{url}"
scraperapi_url = f"https://api.scraperapi.com/?api_key={{api_key}}&url={{url}}"

print("🔗 Fetching actual site via ScraperAPI...")
response = requests.get(scraperapi_url, timeout=30)
print("Status:", response.status_code)
print("Response Preview:\\n", response.text[:500])

# Get credit info
credit_resp = requests.get("https://api.scraperapi.com/account/urlcost", params={{"api_key": api_key, "url": url}})
print("💰 ScraperAPI Credit Info:", credit_resp.json())
'''

        else:  # Custom Proxy
            script_content = f'''import requests

proxies = {json.dumps(proxies, indent=4)}

url = "{url}"
response = requests.get(url, proxies=proxies, verify=False)
print("Status:", response.status_code)
print(response.text[:500])
'''

        # --- Download Script ---
        buffer = BytesIO()
        buffer.write(script_content.encode())
        buffer.seek(0)
        st.download_button(
            label=f"💾 Download Python Script for {platform}",
            data=buffer,
            file_name=f"proxy_credit_checker_{platform.lower().replace('.', '')}.py",
            mime="text/x-python",
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
