import os
import datetime
import pandas as pd
import streamlit as st
import time

# --- 0. Full Screen Canvas Display Configuration ---
st.set_page_config(layout="wide")

# --- Global System Paths & Database Column Schemas ---
DATA_FILE = os.path.join(os.path.dirname(__file__), "ledger_data.csv")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "room_config.csv")
USER_FILE = os.path.join(os.path.dirname(__file__), "accountant_config.csv")

LEDGER_COLUMNS = [
    "Date", "Building", "Room", "Tenant Name", "Phone", "PIN", "Total Man", "Extra Man", 
    "P Reading", "C Reading", "Units", "Electricity", "Clean", "Leftover Arrears", 
    "Extra Surcharge", "Room Rent", "Total Due", "Amount Paid", "Status", "Approved"
]
CONFIG_COLUMNS = ["Building", "Room", "Base Rent"]
USER_COLUMNS = ["Name", "Phone", "Password"]

# --- Initialize Session State Variables ---
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False
if "agent_authenticated" not in st.session_state:
    st.session_state.agent_authenticated = False

# Reactive Core State parameters
if "active_b_sel" not in st.session_state:
    st.session_state.active_b_sel = ""
if "active_r_sel" not in st.session_state:
    st.session_state.active_r_sel = ""
if "live_t_name" not in st.session_state:
    st.session_state.live_t_name = ""
if "live_t_phone" not in st.session_state:
    st.session_state.live_t_phone = ""
if "live_t_arrears" not in st.session_state:
    st.session_state.live_t_arrears = 0.0
if "live_p_reading" not in st.session_state:
    st.session_state.live_p_reading = 0

# --- AUTOMATED DATABASE MAINTENANCE PURGE ROUTINE (6 Months Retention Window) ---
def maintenance_purge_old_records():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            if not df.empty and "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"])
                six_months_ago = pd.Timestamp(datetime.date.today()) - pd.DateOffset(months=6)
                filtered_df = df[df["Date"] >= six_months_ago].copy()
                filtered_df["Date"] = filtered_df["Date"].dt.strftime("%Y-%m-%d")
                filtered_df.to_csv(DATA_FILE, index=False)
        except Exception:
            pass

maintenance_purge_old_records()

# --- 2. Database Loading, Normalization, & Initializers ---
def normalize_ledger(df):
    if df is None: return pd.DataFrame(columns=LEDGER_COLUMNS)
    df = df.copy()
    for col in LEDGER_COLUMNS:
        if col not in df.columns:
            df[col] = 0 if col in ["Total Man", "Extra Man", "P Reading", "C Reading", "Units"] else (0.0 if col not in ["Date", "Building", "Room", "Tenant Name", "Phone", "Status"] else "")
    return df[LEDGER_COLUMNS]

def normalize_config(df):
    if df is None: return pd.DataFrame(columns=CONFIG_COLUMNS)
    df = df.copy()
    for col in CONFIG_COLUMNS:
        if col not in df.columns:
            df[col] = "" if col != "Base Rent" else 0.0
    return df[CONFIG_COLUMNS]

def load_ledger():
    if os.path.exists(DATA_FILE):
        try: return normalize_ledger(pd.read_csv(DATA_FILE))
        except Exception: return pd.DataFrame(columns=LEDGER_COLUMNS)
    return pd.DataFrame(columns=LEDGER_COLUMNS)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try: return normalize_config(pd.read_csv(CONFIG_FILE))
        except Exception: pass
    df = pd.DataFrame(columns=CONFIG_COLUMNS)
    df.to_csv(CONFIG_FILE, index=False)
    return normalize_config(df)

def load_users():
    if os.path.exists(USER_FILE):
        try:
            df = pd.read_csv(USER_FILE)
            for col in USER_COLUMNS:
                if col not in df.columns: df[col] = ""
            return df[USER_COLUMNS]
        except Exception: return pd.DataFrame(columns=USER_COLUMNS)
    df = pd.DataFrame(columns=USER_COLUMNS)
    df.to_csv(USER_FILE, index=False)
    return df

# --- 3. Dynamic English & Hindi Translation Matrix ---
LANG = {
    "English": {
        "title": "🏠 House Rent Book",
        "subtitle": "Accountant Management Dashboard — Secure Offline Collection Engine",
        "view_mode": "Select Active Control Panel View:",
        "tenant_portal": "🚪 Accountant Workspace Entry",
        "admin_portal": "📊 Landlord Panel (Admin)",
        "pass_label": "🔐 Enter Landlord Password Key:",
        "pass_place": "Write password here to unlock...",
        "auth_btn": "Unlock Dashboard",
        "lock_btn": "🔒 Lock & Clear Session",
        "tab1": "📊 Monthly Income Book",
        "tab2": "🚨 Pending Due Watchlist",
        "tab3": "⚙️ Modify Property Assets & Accountants",
        "sec1": "👤 1. Room Occupant Information Profile",
        "sec2": "⚡ 2. Monthly Electricity Units Consumer Input",
        "sec3": "🗃️ 3. Offline Payment Collection Ledger",
        "room_lbl": "Select Target Room Location:",
        "bldg_lbl": "Select Building Complex:",
        "name_lbl": "Tenant Full Name (Editable):",
        "phone_lbl": "Tenant Mobile Number (Editable):",
        "base_lbl": "Total People living in room:",
        "curr_lbl": "Type Total Electricity Units Used This Month:",
        "paid_lbl": "Enter Total Offline Cash/UPI Money Received (₹):",
        "chk_lbl": "✅ I verify that the offline funds recorded above match exactly what was received.",
        "submit_btn": "📤 POST & SAVE ENTRY TO MASTER LEDGER",
        "invoice_title": "📋 Dynamic Calculated Monthly Bill Slip:",
        "inv_rent": "• Base Fixed Room Rent:",
        "inv_arr": "• Past Rolled Unpaid Arrears Balance (+):",
        "inv_extra": "• Extra Occupant Surcharge (+):",
        "inv_elec": "• Electricity Charge (Units Used × ₹10) (+):",
        "inv_clean": "• Standard Room Cleaning Fee (+):",
        "inv_total": "🚨 Total Balance Due From Room:",
        "arr_warn": "⚠️ ARREARS NOTICE: This room carries a rolling unpaid balance of ₹{:,} from last month.",
        "success_msg": "🎉 Transaction successfully posted for Room {} in Building {}!",
        "auth_title": "🔑 Accountant Security Verification Access",
        "auth_phone": "📞 Registered Phone Number:",
        "auth_pin": "🔐 Secure Password PIN:",
        "auth_unlock": "Unlock Portal Session",
        "auth_error": "Invalid Account Credentials. Access Blocked.",
        "auth_empty_error": "⚠️ System Configuration Error: No accountants have been registered yet. Please tell the landlord to log into the Admin panel and add your account first.",
        "standby_msg": "ℹ️ Workspace Standby: Accountant A must select a valid Building and Room to initialize calculations.",
        "ref_msg": "💡 Visual Reference: Last Month's Closing Meter Reading was **{} kWh**",
        "pay_mode_lbl": "Offline Payment Mode Tag:",
        "pay_cash": "Offline Cash",
        "pay_upi": "Offline UPI",
        "err_name": "⚠️ Error: Occupant profile name field cannot remain blank.",
        "err_chk": "⚠️ Error: You must tick the confirmation box declaration.",
        "status_clear": "Cleared",
        "status_debt": "Partial Debt"
    },
    "Hindi": {
        "title": "🏠 कमरे का किराया खाता बुक",
        "subtitle": "अकाउंटेंट मैनेजमेंट डैशबोर्ड — सुरक्षित ऑफलाइन एंट्री इंजन",
        "view_mode": "कंट्रोल पैनल व्यू का चयन करें:",
        "tenant_portal": "🚪 अकाउंटेंट वर्कस्पेस एंट्री",
        "admin_portal": "📊 मकान मालिक डैशबोर्ड (Admin Panel)",
        "pass_label": "🔐 मकान मालिक का गुप्त पासवर्ड डालें:",
        "pass_place": "अनलॉक करने के लिए यहां पासवर्ड लिखें...",
        "auth_btn": "खाता अनलॉक करें",
        "lock_btn": "🔒 सेशन लॉक करें और क्रेडेंशियल मिटाएं",
        "tab1": "📊 कमाई का पूरा लेजर विवरण",
        "tab2": "🚨 उधारी/डिफॉल्टर लिस्ट",
        "tab3": "⚙️ प्रॉपर्टी रूम व अकाउंटेंट मैनेजर",
        "sec1": "👤 1. किरायेदार प्रोफाइल जानकारी (बदले हेतु टाइप करें)",
        "sec2": "⚡ 2. इस महीने उपयोग की गई बिजली यूनिट",
        "sec3": "🗃️ 3. ऑफलाइन पैसा कलेक्शन एंट्री",
        "room_lbl": "कमरा नंबर चुनें:",
        "bldg_lbl": "बिल्डिंग का नाम चुनें:",
        "name_lbl": "किरायेदार का पूरा नाम (बदलने हेतु टाइप करें):",
        "phone_lbl": "किरायेदार का मोबाइल नंबर:",
        "base_lbl": "कमरे में रहने वाले कुल लोग:",
        "curr_lbl": "इस महीने उपयोग की गई कुल बिजली यूनिट यहाँ लिखें:",
        "paid_lbl": "किरायेदार से ऑफलाइन नकद/UPI कितने रूपये प्राप्त किये? (₹):",
        "chk_lbl": "✅ मैं पुष्टि करता हूँ कि मैंने ऊपर लिखे पूरे पैसे ऑफलाइन प्राप्त कर लिए हैं।",
        "submit_btn": "📤 कलेक्शन एंट्री सुरक्षित करें (SUBMIT)",
        "invoice_title": "📋 इस महीने का कुल बिल पर्चा (Bill Slip):",
        "inv_rent": "• कमरे का तय किराया:",
        "inv_arr": "• पिछले महीने का बकाया (+):",
        "inv_extra": "• अतिरिक्त लोगों का चार्ज (+):",
        "inv_elec": "• बिजली का खर्चा (यूनिट × ₹10) (+):",
        "inv_clean": "• कमरे की सफाई का खर्च (+):",
        "inv_total": "🚨 किरायेदार से वसूलने योग्य कुल राशि:",
        "arr_warn": "⚠️ बकाया सूचना: इस कमरे का पिछला बकाया ₹{:,} बकाया बचा हुआ है।",
        "success_msg": "🎉 बधाई हो! कमरा नंबर {} ({}) की रेंट कलेक्शन एंट्री सुरक्षित जमा हो गई है।",
        "auth_title": "🔑 अकाउंटेंट सुरक्षा सत्यापन एक्सेस",
        "auth_phone": "📞 पंजीकृत मोबाइल नंबर:",
        "auth_pin": "🔐 गुप्त पासवर्ड पिन डालें:",
        "auth_unlock": "पोर्टल सेशन अनलॉक करें",
        "auth_error": "अमान्य खाता क्रेडेंशियल। एक्सेस अवरुद्ध।",
        "auth_empty_error": "⚠️ सिस्टम त्रुटि: अभी तक कोई भी अकाउंटेंट पंजीकृत नहीं है। कृपया मकान मालिक से एडमिन पैनल में जाकर अपना मोबाइल नंबर व पासवर्ड रजिस्टर करवाएं।",
        "standby_msg": "ℹ️ वर्कस्पेस स्टैंडबाय: गणना शुरू करने के लिए अकाउंटेंट A को एक वैध बिल्डिंग और कमरा चुनना होगा।",
        "ref_msg": "💡 विजुअल संदर्भ: पिछले महीने की अंतिम मीटर रीडिंग **{} kWh** थी",
        "pay_mode_lbl": "ऑफलाइन भुगतान का प्रकार:",
        "pay_cash": "ऑफलाइन नकद (Cash)",
        "pay_upi": "ऑफलाइन यूपीआई (UPI)",
        "err_name": "⚠️ त्रुटि: किरायेदार का नाम खाली नहीं छोड़ा जा सकता।",
        "err_chk": "⚠️ त्रुटि: आपको पुष्टि घोषणा बॉक्स को टिक करना होगा।",
        "status_clear": "चुक्ता (Cleared)",
        "status_debt": "बकाया (Partial Debt)"
    }
}

# --- 4. Reactive Lookup Hooks Engine ---
def sync_reactive_room_state():
    b_target = st.session_state.get("ui_building_select")
    r_target = st.session_state.get("ui_room_select")
    
    if not b_target or not r_target or b_target == "" or r_target == "":
        st.session_state.live_t_name = ""
        st.session_state.live_t_phone = ""
        st.session_state.live_t_arrears = 0.0
        st.session_state.live_p_reading = 0
        return
        
    df = load_ledger()
    st.session_state.live_t_name = ""
    st.session_state.live_t_phone = ""
    st.session_state.live_t_arrears = 0.0
    st.session_state.live_p_reading = 0
    
    if not df.empty:
        history = df[(df["Building"] == b_target) & (df["Room"] == r_target)].copy()
        if not history.empty:
            history = history.sort_values("Date")
            latest = history.iloc[-1]
            st.session_state.live_t_name = str(latest.get("Tenant Name", ""))
            st.session_state.live_t_phone = str(latest.get("Phone", ""))
            try: st.session_state.live_p_reading = int(latest["C Reading"])
            except: st.session_state.live_p_reading = 0
            try:
                due = float(latest["Total Due"])
                paid = float(latest["Amount Paid"])
                st.session_state.live_t_arrears = round(due - paid, 2)
            except:
                st.session_state.live_t_arrears = 0.0

# --- 5. High-Contrast Custom CSS Injection Sheet ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #0F172A; padding: 22px; border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); text-align: center;
        border: 2px solid #334155; margin-bottom: 15px;
    }
    .metric-value-green { font-size: 28px; font-weight: 800; color: #4ADE80; }
    .metric-value-red { font-size: 28px; font-weight: 800; color: #F87171; }
    .metric-value-blue { font-size: 28px; font-weight: 800; color: #60A5FA; }
    .metric-value-purple { font-size: 28px; font-weight: 800; color: #C084FC; }
    .metric-label { font-size: 13px; font-weight: 700; color: #E2E8F0; text-transform: uppercase; margin-top: 5px; }
    
    .invoice-box { border: 2px dashed #16A34A; padding: 22px; border-radius: 12px; margin-bottom: 15px; }
    .arrears-box { border: 2px solid #EF4444; padding: 12px; border-radius: 8px; margin-bottom: 12px; color: #EF4444; font-weight: 700; }
    
    div.stButton > button:first-child {
        background-color: #2563EB; color: white; font-weight: 700; font-size: 17px;
        padding: 12px 24px; border-radius: 10px; border: none; width: 100%;
    }
    div.stButton > button:first-child:hover { background-color: #1D4ED8; }
    </style>
""", unsafe_allow_html=True)

# --- 6. Interface Workspace Router Placement ---
selected_lang = st.radio("🌐 Choose Interface Language / भाषा चुनें:", ["English", "Hindi"], horizontal=True)
T = LANG[selected_lang]

st.markdown("---")
portal_options = ["tenant", "admin"]
portal_labels = {"tenant": T["tenant_portal"], "admin": T["admin_portal"]}

if "current_portal_index" not in st.session_state:
    st.session_state.current_portal_index = 0

chosen_portal_key = st.selectbox(
    T["view_mode"], portal_options, 
    index=st.session_state.current_portal_index,
    format_func=lambda x: portal_labels[x]
)
st.session_state.current_portal_index = portal_options.index(chosen_portal_key)
portal_mode = portal_labels[chosen_portal_key]

# ----------------- 🚪 RE-ARCHITECTED ACCOUNTANT A ENTRY PORTAL -----------------
if portal_mode == T["tenant_portal"]:
    st.title(T["title"])
    st.caption(T["subtitle"])

    config_df = load_config()
    ledger_df = load_ledger()
    user_df = load_users()
    
    if not st.session_state.agent_authenticated:
        st.markdown(f"### {T['auth_title']}")
        
        if user_df.empty:
            st.error(T["auth_empty_error"])
        else:
            col_ag_p, col_ag_k = st.columns(2)
            with col_ag_p:
                input_ag_phone = st.text_input(T["auth_phone"], key="auth_field_phone")
            with col_ag_k:
                input_ag_pin = st.text_input(T["auth_pin"], type="password", key="auth_field_password")
                
            if st.button(T["auth_unlock"]):
                is_valid_user = False
                match = user_df[(user_df["Phone"].astype(str) == input_ag_phone.strip()) & (user_df["Password"].astype(str) == input_ag_pin.strip())]
                if not match.empty: 
                    is_valid_user = True
                    
                if is_valid_user:
                    st.session_state.agent_authenticated = True
                    st.success("Success!")
                    st.rerun()
                else:
                    st.error(T["auth_error"])
    else:
        if st.sidebar.button(T["lock_btn"]):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
            
        if config_df.empty:
            st.info("No configured asset rooms.")
        else:
            st.markdown("### 🏢 Room Selection & Data Entry Workspace")
            
            b_list = [""] + sorted(list(config_df["Building"].unique()))
            col_sel_b, col_sel_r = st.columns(2)
            with col_sel_b:
                selected_building = st.selectbox(
                    T["bldg_lbl"], b_list, 
                    key="ui_building_select", 
                    on_change=sync_reactive_room_state
                )
                st.session_state.active_b_sel = selected_building
                
            with col_sel_r:
                if st.session_state.active_b_sel and st.session_state.active_b_sel != "":
                    r_list = [""] + sorted(list(config_df[config_df["Building"] == st.session_state.active_b_sel]["Room"].unique()))
                else:
                    r_list = [""]
                selected_room = st.selectbox(T["room_lbl"], r_list, key="ui_room_select", on_change=sync_reactive_room_state)
                st.session_state.active_r_sel = selected_room

            if not st.session_state.active_b_sel or st.session_state.active_b_sel == "" or not st.session_state.active_r_sel or st.session_state.active_r_sel == "":
                st.info(T["standby_msg"])
            else:
                room_config = config_df[(config_df["Building"] == st.session_state.active_b_sel) & (config_df["Room"] == st.session_state.active_r_sel)].iloc[-1]
                base_room_rent = float(room_config["Base Rent"])
                auto_p_read = st.session_state.live_p_reading
                leftover_arrears = st.session_state.live_t_arrears

                st.markdown("---")
                st.markdown(f"### {T['sec1']}")
                t_name = st.text_input(T["name_lbl"], value=st.session_state.live_t_name, key="input_field_tenant_name")
                t_phone = st.text_input(T["phone_lbl"], value=st.session_state.live_t_phone, key="input_field_tenant_phone")
                
                total_man = st.number_input(T["base_lbl"], min_value=1, max_value=20, value=1)
                
                # --- AUTOMATED OCCUPANT CAPACITY CALCULATION ---
                if total_man > 3:
                    extra_man = total_man - 3
                else:
                    extra_man = 0

                st.markdown("---")
                if leftover_arrears > 0:
                    st.markdown(f"""<div class="arrears-box">{T["arr_warn"].format(leftover_arrears)}</div>""", unsafe_allow_html=True)
                    
                st.markdown(f"### {T['sec2']}")
                st.info(T["ref_msg"].format(auto_p_read))
                consumed_units = st.number_input(T["curr_lbl"], min_value=0, value=0)

                fixed_clean_fee = 70.0
                unit_charge_rate = 10.0
                extra_person_surcharge_revenue = float(extra_man * 500)
                calculated_electricity_bill = float(consumed_units * unit_charge_rate)
                grand_total_payable = base_room_rent + extra_person_surcharge_revenue + calculated_electricity_bill + fixed_clean_fee + leftover_arrears

                st.markdown(f"""
                <div class="invoice-box">
                    <h3 style='color:#16A34A; margin-top:0;'>{T["invoice_title"]}</h3>
                    <p style='font-size: 16px; line-height: 1.8;'>
                    <b>{T["inv_rent"]}</b> ₹{base_room_rent:,}<br>
                    <b>{T["inv_arr"]}</b> ₹{leftover_arrears:,}<br>
                    <b>{T["inv_extra"]} (₹500 × {extra_man} Extra):</b> ₹{extra_person_surcharge_revenue:,}<br>
                    <b>{T["inv_elec"]} ({consumed_units} Units × ₹{unit_charge_rate}):</b> ₹{calculated_electricity_bill:,}<br>
                    <b>{T["inv_clean"]}</b> ₹{fixed_clean_fee}<br>
                    </p>
                    <hr style="border:1px dashed #16A34A; margin:10px 0;">
                    <h2 style='color:#16A34A; margin-bottom:0;'>{T["inv_total"]} ₹{grand_total_payable:,}</h2>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"### {T['sec3']}")
                col_pmode, col_pamt = st.columns(2)
                with col_pmode: pay_method = st.radio(T["pay_mode_lbl"], [T["pay_cash"], T["pay_upi"]])
                with col_pamt: amount_paid_by_user = st.number_input(T["paid_lbl"], min_value=0.0, value=float(grand_total_payable))
                
                confirmation_check = st.checkbox(T["chk_lbl"])
                submit_bill = st.button(T["submit_btn"])

                if submit_bill:
                    if not t_name.strip(): st.error(T["err_name"])
                    elif not confirmation_check: st.error(T["err_chk"])
                    else:
                        current_date = datetime.date.today().strftime("%Y-%m-%d")
                        status_label = T["status_clear"] if amount_paid_by_user >= grand_total_payable else T["status_debt"]
                        entry = {
                            "Date": current_date, "Building": st.session_state.active_b_sel, "Room": st.session_state.active_r_sel,
                            "Tenant Name": t_name.strip(), "Phone": str(t_phone.strip()), "PIN": f"A_{pay_method}",
                            "Total Man": int(total_man), "Extra Man": int(extra_man),
                            "P Reading": int(auto_p_read), "C Reading": int(auto_p_read + consumed_units), "Units": int(consumed_units),
                            "Electricity": float(calculated_electricity_bill), "Clean": float(fixed_clean_fee),
                            "Leftover Arrears": float(leftover_arrears), "Extra Surcharge": float(extra_person_surcharge_revenue),
                            "Room Rent": float(base_room_rent), "Total Due": float(grand_total_payable),
                            "Amount Paid": float(amount_paid_by_user), "Status": status_label, "Approved": "Yes"
                        }
                        new_ledger = pd.concat([load_ledger(), pd.DataFrame([entry])], ignore_index=True)
                        new_ledger.to_csv(DATA_FILE, index=False)
                        st.success(T["success_msg"].format(st.session_state.active_r_sel, st.session_state.active_b_sel))
                        st.balloons()
                        
                        # --- SAFE WIPE RESET PROTOCOL ---
                        for key_to_clear in ["ui_building_select", "ui_room_select", "active_b_sel", "active_r_sel", "live_t_name", "live_t_phone", "live_t_arrears", "live_p_reading"]:
                            if key_to_clear in st.session_state:
                                del st.session_state[key_to_clear]
                        
                        time.sleep(1)
                        st.rerun()

# ----------------- 📊 PROPERTY OWNER ADMIN CONTROL CENTER -----------------
elif portal_mode == T["admin_portal"]:
    if not st.session_state.admin_authenticated:
        with st.form("full_width_admin_auth_form"):
            admin_pin = st.text_input(T["pass_label"], type="password", placeholder=T["pass_place"])
            submit_clicked = st.form_submit_button(T["auth_btn"])
            if submit_clicked:
                try: secure_master_pin = st.secrets["admin"]["password"]
                except Exception: secure_master_pin = "0000"
                if admin_pin == secure_master_pin:
                    st.session_state.admin_authenticated = True
                    st.success("Access Granted / लॉगिन सफल।")
                    st.rerun()
                else: st.error("❌ Authentication Failed.")
    else:
        if st.sidebar.button(T["lock_btn"]):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

        admin_tab1, admin_tab2, admin_tab3 = st.tabs([T["tab1"], T["tab2"], T["tab3"]])
        ledger_df = load_ledger()
        config_df = load_config()
        user_df = load_users()

        with admin_tab1:
            if ledger_df.empty: calc_total_due = calc_total_paid = calc_arrears = 0.0
            else:
                calc_total_due = float(ledger_df["Total Due"].sum())
                calc_total_paid = float(ledger_df["Amount Paid"].sum())
                calc_arrears = max(0.0, calc_total_due - calc_total_paid)

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f'<div class="metric-card"><div class="metric-value-blue">₹{calc_total_due:,.2f}</div><div class="metric-label">💰 Portfolio Receivables</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><div class="metric-value-green">₹{calc_total_paid:,.2f}</div><div class="metric-label">🏦 Realized Collections</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="metric-card"><div class="metric-value-red">₹{calc_arrears:,.2f}</div><div class="metric-label">🚨 Outstanding Debt Balance</div></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="metric-card"><div class="metric-value-purple">{len(config_df)}</div><div class="metric-label">🏢 Configured Asset Rooms</div></div>', unsafe_allow_html=True)

            if not ledger_df.empty:
                st.markdown("### 📥 Monthly Data Archive Exporter")
                export_tracker_df = ledger_df.copy()
                export_tracker_df["Export_Month"] = pd.to_datetime(export_tracker_df["Date"]).dt.strftime("%Y-%m")
                available_months = sorted(list(export_tracker_df["Export_Month"].unique()), reverse=True)
                selected_export_month = st.selectbox("📅 Choose Target Month:", available_months)
                monthly_filtered_data = export_tracker_df[export_tracker_df["Export_Month"] == selected_export_month].copy()
                st.download_button(label=f"Download {selected_export_month} Ledger (.csv)", data=monthly_filtered_data.to_csv(index=False).encode('utf-8'), file_name=f"Ledger_{selected_export_month}.csv", mime="text/csv")
                st.dataframe(ledger_df.sort_values(by="Date", ascending=False), use_container_width=True)

        with admin_tab2:
            st.markdown("### 🚨 Active Defaulters Watchlist")
            if not config_df.empty and not ledger_df.empty:
                defaulter_records_list = []
                for _, room_row in config_df.iterrows():
                    b_name = room_row["Building"]
                    r_name = room_row["Room"]
                    room_history = ledger_df[(ledger_df["Building"] == b_name) & (ledger_df["Room"] == r_name)]
                    if not room_history.empty:
                        latest_entry = room_history.sort_values("Date").iloc[-1]
                        debt_amt = round(float(latest_entry["Total Due"]) - float(latest_entry["Amount Paid"]), 2)
                        if debt_amt > 0.01:
                            defaulter_records_list.append({"Building": b_name, "Room": r_name, "Tenant Name": latest_entry["Tenant Name"], "Remaining Balance Debt": debt_amt})
                if defaulter_records_list: st.dataframe(pd.DataFrame(defaulter_records_list), use_container_width=True)
                else: st.success("🎉 Zero active units carry unpaid balances.")

        with admin_tab3:
            st.markdown("### ⚙️ Interactive Rent Setup & Identity Manager")
            
            st.markdown("#### 🏢 Add / Modify Building Asset Units")
            with st.form("add_room_form"):
                b_input = st.text_input("Building Name:")
                r_input = st.text_input("Room Identifier Tag:")
                rent_input = st.number_input("Base Rent Rate (₹):", min_value=0.0, value=2500.0)
                if st.form_submit_button("💾 Save Asset Unit"):
                    if b_input.strip() and r_input.strip():
                        fresh_config = load_config()
                        fresh_config = fresh_config[~((fresh_config["Building"].str.upper() == b_input.strip().title().upper()) & (fresh_config["Room"].str.upper() == r_input.strip().title().upper()))]
                        new_row = pd.DataFrame([{"Building": b_input.strip().title(), "Room": r_input.strip().title(), "Base Rent": float(rent_input)}])
                        pd.concat([fresh_config, new_row], ignore_index=True).to_csv(CONFIG_FILE, index=False)
                        st.success("Asset configuration saved!")
                        st.rerun()

            st.markdown("#### 🗑️ Permanently Remove Property Rooms")
            if not config_df.empty:
                col_del_b, col_del_r = st.columns(2)
                with col_del_b: db_b = st.selectbox("Select Target Building for Delete:", sorted(list(config_df["Building"].unique())))
                with col_del_r: db_r = st.selectbox("Select Target Room for Delete:", sorted(list(config_df[config_df["Building"] == db_b]["Room"].unique())))
                if st.button("❌ Permanently Delete Selected Room Profile"):
                    purged_config = config_df[~((config_df["Building"] == db_b) & (config_df["Room"] == db_r))]
                    purged_config.to_csv(CONFIG_FILE, index=False)
                    st.warning(f"Purged Room Asset Profile {db_b} - {db_r} successfully.")
                    time.sleep(1)
                    st.rerun()

            st.markdown("---")
            
            st.markdown("#### 👤 Add New Authorized Accountant Account")
            with st.form("add_user_form"):
                u_name = st.text_input("Accountant Person Name:")
                u_phone = st.text_input("Login Mobile Number (10 Digits):")
                u_pass = st.text_input("Create Secret Verification Password Key:")
                if st.form_submit_button("💾 Authorize Accountant Account"):
                    if u_name.strip() and len(u_phone.strip()) == 10 and u_pass.strip():
                        fresh_users = load_users()
                        fresh_users = fresh_users[fresh_users["Phone"].astype(str) != u_phone.strip()]
                        new_user = pd.DataFrame([{"Name": u_name.strip(), "Phone": str(u_phone.strip()), "Password": str(u_pass.strip())}])
                        pd.concat([fresh_users, new_user], ignore_index=True).to_csv(USER_FILE, index=False)
                        st.success(f"Authorized Accountant {u_name} successfully.")
                        time.sleep(1)
                        st.rerun()

            st.markdown("#### 📝 Modify Existing Accountant Password Key")
            if not user_df.empty:
                with st.form("modify_user_password_form"):
                    selected_mod_phone = st.selectbox("Select Accountant Phone Number to Update:", user_df["Phone"].unique())
                    new_password_input = st.text_input("Type New Secret Password Key:", type="password", placeholder="Enter new password...")
                    
                    if st.form_submit_button("🔄 Update Accountant Password"):
                        if new_password_input.strip():
                            fresh_users = load_users()
                            fresh_users.loc[fresh_users["Phone"].astype(str) == str(selected_mod_phone), "Password"] = str(new_password_input.strip())
                            fresh_users.to_csv(USER_FILE, index=False)
                            st.success("Accountant security verification key successfully updated!")
                            time.sleep(1)
                            st.rerun()
                        else: st.error("⚠️ Password cannot be left blank.")
            else: st.info("No active custom accountants registered to modify.")

            st.markdown("#### 🗑️ De-Authorize Accountant Accounts")
            if not user_df.empty:
                rem_phone = st.selectbox("Select Accountant Mobile to De-Authorize:", user_df["Phone"].unique())
                if st.button("❌ Revoke Accountant Access Permanently"):
                    purged_users = user_df[user_df["Phone"].astype(str) != str(rem_phone)]
                    purged_users.to_csv(USER_FILE, index=False)
                    st.error("Account Access Context Revoked.")
                    time.sleep(1)
                    st.rerun()
            else: st.info("No active custom accountants registered.")
