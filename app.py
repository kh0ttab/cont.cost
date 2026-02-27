import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

st.set_page_config(
    page_title="Container Economics Calculator",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

def find_data_file(filename='fees_data.json'):
    possible_paths = [
        os.path.join(os.path.dirname(__file__), 'data', filename),
        os.path.join(os.path.dirname(__file__), '..', 'data', filename),
        os.path.join(os.path.dirname(__file__), filename),
        os.path.join(os.getcwd(), 'data', filename),
        os.path.join(os.getcwd(), filename),
        filename
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return possible_paths[0]

DATA_FILE = find_data_file('fees_data.json')

DEFAULT_FEES_DATA = {
    "containers": {
        "20ft": {"volume_cuft": 1170, "payload_lbs": 42100},
        "40ft": {"volume_cuft": 2350, "payload_lbs": 50100},
        "40hc": {"volume_cuft": 2690, "payload_lbs": 50100}
    },
    "tariff_rates": {"default": 21.0, "categories": {"electronics": 7.5, "machinery": 7.5, "furniture": 10.0, "textiles": 16.5, "footwear": 16.5, "toys": 11.0, "plastics": 6.5}},
    "import_fees": {"customs_bond_fee": 250.0, "customs_entry_fee": 150.0, "isi_fee": 150.0, "merchandise_processing_fee": 0.0034, "harbor_maintenance_fee": 0.00125, "import_security_fee": 0.0025},
    "shipping_costs": {"chinese_warehousing_per_day_per_cuft": 0.02, "insurance_rate": 0.0035},
    "fba_fees": {"referral_fee_percent": {"default": 0.15, "category_overrides": {"electronics": 0.08}}, "fulfillment_fees": [{"weight_oz": 16, "fee": 3.22}, {"weight_oz": 64, "fee": 4.63}, {"weight_oz": 128, "fee": 5.53}, {"weight_oz": 256, "fee": 6.85}, {"weight_oz": 512, "fee": 11.37}, {"weight_oz": 99999, "fee": 58.32}], "storage_fees_monthly_per_cuft": {"jan_sep": 0.75}},
    "wfs_fees": {"referral_fee_percent": {"default": 0.15, "electronics": 0.06}, "fulfillment_fees_per_lb": 0.75, "pick_and_pack_fee": 1.50, "storage_fees_monthly_per_cuft": {"standard": 0.50}, "weight_handling": {"first_lb": 1.50, "additional_lb": 0.50}}
}

def load_fees_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return DEFAULT_FEES_DATA

def calculate_container_fit(items, container_type, utilization_target):
    fees_data = load_fees_data()
    container = fees_data['containers'][container_type]
    
    max_volume_cuft = container['volume_cuft']
    max_weight_lbs = container['payload_lbs']
    
    total_item_volume = sum(item['volume_cuft'] * item['quantity'] for item in items)
    total_item_weight = sum(item['weight_lbs'] * item['quantity'] for item in items)
    
    volume_limit = max_volume_cuft * utilization_target
    weight_limit = max_weight_lbs * utilization_target
    
    volume_fit = int(volume_limit / items[0]['volume_cuft']) if items else 0
    weight_fit = int(weight_limit / items[0]['weight_lbs']) if items else 0
    
    total_fit = max(1, min(volume_fit, weight_fit))
    used_volume = total_fit * items[0]['volume_cuft']
    used_weight = total_fit * items[0]['weight_lbs']
    
    return {
        'total_items_fit': total_fit,
        'space_utilization_percent': round((used_volume / max_volume_cuft) * 100, 2),
        'weight_utilization_percent': round((used_weight / max_weight_lbs) * 100, 2),
        'remaining_volume_cuft': round(max_volume_cuft - used_volume, 2),
        'total_weight_lbs': round(used_weight, 2),
        'max_weight_lbs': max_weight_lbs
    }

def calculate_import_costs(item, container_result, china_warehouse_days=7, ocean_freight=35.0, inland_trucking=1200.0):
    fees_data = load_fees_data()
    import_fees = fees_data['import_fees']
    shipping_costs = fees_data['shipping_costs']
    tariff_rates = fees_data['tariff_rates']
    
    total_units = container_result['total_items_fit']
    total_cost = item['unit_cost_usd'] * total_units
    item_volume = item['volume_cuft'] * total_units
    
    ocean_freight_cost = item_volume * ocean_freight
    chinese_warehousing = item_volume * shipping_costs['chinese_warehousing_per_day_per_cuft'] * china_warehouse_days
    insurance = (total_cost + ocean_freight_cost) * shipping_costs['insurance_rate']
    
    mpf = (total_cost + ocean_freight_cost) * import_fees['merchandise_processing_fee']
    hmf = (total_cost + ocean_freight_cost) * import_fees['harbor_maintenance_fee']
    isf = (total_cost + ocean_freight_cost) * import_fees['import_security_fee']
    port_to_warehouse = (item_volume / 35.315) * 150
    
    cif_value = total_cost + ocean_freight_cost + insurance
    category = item['product_category'].lower()
    tariff_rate = tariff_rates['categories'].get(category, tariff_rates['default'])
    tariff_amount = cif_value * (tariff_rate / 100)
    
    total_import = (total_cost + ocean_freight_cost + chinese_warehousing + insurance +
                    import_fees['customs_bond_fee'] + import_fees['customs_entry_fee'] +
                    import_fees['isi_fee'] + mpf + hmf + isf + port_to_warehouse +
                    inland_trucking + tariff_amount)
    
    return {
        'item_cost_usd': total_cost,
        'ocean_freight_usd': round(ocean_freight_cost, 2),
        'chinese_warehousing_usd': round(chinese_warehousing, 2),
        'insurance_usd': round(insurance, 2),
        'customs_bond_usd': import_fees['customs_bond_fee'],
        'customs_entry_usd': import_fees['customs_entry_fee'],
        'isi_fee_usd': import_fees['isi_fee_usd'],
        'merchandise_processing_usd': round(mpf, 2),
        'harbor_maintenance_usd': round(hmf, 2),
        'import_security_usd': round(isf, 2),
        'port_to_warehouse_usd': round(port_to_warehouse, 2),
        'inland_trucking_usd': inland_trucking,
        'tariff_rate_percent': tariff_rate,
        'tariff_amount_usd': round(tariff_amount, 2),
        'total_import_cost_usd': round(total_import, 2),
        'per_unit_import_cost_usd': round(total_import / total_units, 2)
    }

def calculate_amazon_fba(item, selling_price):
    fees_data = load_fees_data()
    fba = fees_data['fba_fees']
    category = item['product_category'].lower()
    referral_rate = fba['referral_fee_percent']['category_overrides'].get(category, fba['referral_fee_percent']['default'])
    
    weight_oz = item['weight_lbs'] * 16
    fulfillment_fee = next((t['fee'] for t in fba['fulfillment_fees'] if weight_oz <= t['weight_oz']), 3.22)
    storage_fee = item['volume_cuft'] * fba['storage_fees_monthly_per_cuft']['jan_sep']
    total = selling_price * referral_rate + fulfillment_fee + storage_fee
    
    return {
        'referral_fee_usd': round(selling_price * referral_rate, 2),
        'referral_fee_percent': referral_rate * 100,
        'fulfillment_fee_usd': round(fulfillment_fee, 2),
        'storage_fee_monthly_usd': round(storage_fee, 2),
        'per_unit_fees_usd': round(total, 2)
    }

def calculate_walmart_wfs(item, selling_price):
    fees_data = load_fees_data()
    wfs = fees_data['wfs_fees']
    category = item['product_category'].lower()
    referral_rate = wfs['referral_fee_percent'].get(category, wfs['referral_fee_percent']['default'])
    
    referral_fee = selling_price * referral_rate
    fulfillment_fee = item['weight_lbs'] * wfs['fulfillment_fees_per_lb']
    pick_pack_fee = wfs['pick_and_pack_fee']
    storage_fee = item['volume_cuft'] * wfs['storage_fees_monthly_per_cuft']['standard']
    weight_handling = wfs['weight_handling']['first_lb'] + max(0, item['weight_lbs'] - 1) * wfs['weight_handling']['additional_lb']
    
    total = referral_fee + fulfillment_fee + pick_pack_fee + storage_fee + weight_handling
    
    return {
        'referral_fee_usd': round(referral_fee, 2),
        'referral_fee_percent': referral_rate * 100,
        'fulfillment_fee_usd': round(fulfillment_fee, 2),
        'pick_pack_fee_usd': round(pick_pack_fee, 2),
        'storage_fee_monthly_usd': round(storage_fee, 2),
        'weight_handling_usd': round(weight_handling, 2),
        'per_unit_fees_usd': round(total, 2)
    }


st.title("📦 Container Economics Calculator")
st.markdown("### Import from China to USA - Space & Cost Analysis")

with st.sidebar:
    st.header("⚙️ Configuration")
    container_type = st.selectbox("Container Type", ["20ft", "40ft", "40hc"], index=2)
    utilization_target = st.slider("Target Utilization %", 50, 100, 90) / 100
    china_warehouse_days = st.number_input("China Warehouse (days)", 0, 90, 7)
    ocean_freight = st.number_input("Ocean Freight ($/cu ft)", 10.0, 100.0, 35.0, 5.0)
    inland_trucking = st.number_input("Inland Trucking ($)", 500.0, 3000.0, 1200.0, 100.0)
    include_amazon = st.checkbox("Amazon FBA Fees", value=True)
    include_walmart = st.checkbox("Walmart WFS Fees", value=True)

st.subheader("📋 Add Items")

c1, c2, c3, c4, c5 = st.columns(5)
with c1: item_name = st.text_input("Item Name", "Product A")
with c2: length = st.number_input("Length (in)", 1.0, 120.0, 12.0, 1.0)
with c3: width = st.number_input("Width (in)", 1.0, 120.0, 12.0, 1.0)
with c4: height = st.number_input("Height (in)", 1.0, 120.0, 12.0, 1.0)
with c5: weight = st.number_input("Weight (lbs)", 0.1, 100.0, 2.0, 0.5)

c6, c7, c8, c9 = st.columns(4)
categories = ["default", "electronics", "machinery", "furniture", "textiles", "footwear", "toys", "plastics", "steel", "aluminum"]
with c6: quantity = st.number_input("Quantity", 1, 100000, 100, 10)
with c7: unit_cost = st.number_input("Unit Cost ($)", 0.1, 10000.0, 10.0, 1.0)
with c8: category = st.selectbox("Category", categories)
with c9:
    st.write("")
    st.write("")
    if st.button("➕ Add Item", type="primary"):
        if 'items' not in st.session_state: st.session_state.items = []
        volume_cuft = (length * width * height) / 1728
        st.session_state.items.append({
            "name": item_name, "length_in": length, "width_in": width, "height_in": height,
            "weight_lbs": weight, "quantity": quantity, "unit_cost_usd": unit_cost,
            "product_category": category, "volume_cuft": volume_cuft
        })
        st.success(f"Added {item_name}!")

if 'items' not in st.session_state: st.session_state.items = []

if st.session_state.items:
    st.subheader("📦 Items in Order")
    df = pd.DataFrame(st.session_state.items)
    df['Total Volume'] = df['volume_cuft'] * df['quantity']
    df['Total Weight'] = df['weight_lbs'] * df['quantity']
    df['Total Cost'] = df['unit_cost_usd'] * df['quantity']
    st.dataframe(df[['name', 'length_in', 'width_in', 'height_in', 'weight_lbs', 'quantity', 'unit_cost_usd', 'product_category', 'Total Volume', 'Total Weight', 'Total Cost']], use_container_width=True)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Volume", f"{df['Total Volume'].sum():.2f} cu ft")
    c2.metric("Total Weight", f"{df['Total Weight'].sum():.2f} lbs")
    c3.metric("Total Cost", f"${df['Total Cost'].sum():,.2f}")
    
    if st.button("🗑️ Clear All"):
        st.session_state.items = []
        st.rerun()

if st.session_state.items and st.button("🚀 Calculate", type="primary", use_container_width=True):
    fees_data = load_fees_data()
    max_vol = fees_data['containers'][container_type]['volume_cuft']
    space_needed = sum(i['volume_cuft'] * i['quantity'] for i in st.session_state.items) * utilization_target
    
    if space_needed > max_vol:
        st.error(f"❌ Exceeds container! Need {space_needed:.0f} cu ft, max {max_vol} cu ft")
    else:
        item = st.session_state.items[0]
        container_result = calculate_container_fit(st.session_state.items, container_type, utilization_target)
        import_costs = calculate_import_costs(item, container_result, china_warehouse_days, ocean_freight, inland_trucking)
        selling_price = item['unit_cost_usd'] * 3
        
        amazon_fba = {}
        walmart_wfs = {}
        if include_amazon: amazon_fba = calculate_amazon_fba(item, selling_price)
        if include_walmart: walmart_wfs = calculate_walmart_wfs(item, selling_price)
        
        total_cost = import_costs['per_unit_import_cost_usd']
        if include_amazon: total_cost += amazon_fba['per_unit_fees_usd']
        suggested_price = total_cost / 0.7
        gross_margin = selling_price - total_cost
        gross_margin_pct = (gross_margin / selling_price * 100) if selling_price > 0 else 0
        
        st.success("✅ Calculation Complete!")
        st.markdown("---")
        st.subheader("📊 Container Space Analysis")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Items Fit", f"{container_result['total_items_fit']}")
        c2.metric("Space Used", f"{container_result['space_utilization_percent']}%")
        c3.metric("Weight Used", f"{container_result['weight_utilization_percent']}%")
        c4.metric("Remaining", f"{container_result['remaining_volume_cuft']} cu ft")
        
        fig = go.Figure(go.Indicator(mode="gauge+number", value=container_result['space_utilization_percent'],
            title={'text': "Space Utilization %"}, gauge={'axis': {'range': [0, 100]},
            'bar': {'color': "#1f77b4"}, 'steps': [{'range': [0, 70], 'color': "#ffccc7"},
            {'range': [70, 90], 'color': "#fff7b6"}, {'range': [90, 100], 'color': "#d9f7be"}]}))
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.subheader("💰 Import Cost Breakdown")
        
        costs = {'Item Cost': import_costs['item_cost_usd'], 'Ocean Freight': import_costs['ocean_freight_usd'],
            'China Warehousing': import_costs['chinese_warehousing_usd'], 'Insurance': import_costs['insurance_usd'],
            'Customs Bond': import_costs['customs_bond_usd'], 'MPF': import_costs['merchandise_processing_usd'],
            'Harbor Maint.': import_costs['harbor_maintenance_usd'], 'Import Security': import_costs['import_security_usd'],
            'Port to Whse': import_costs['port_to_warehouse_usd'], 'Inland Trucking': import_costs['inland_trucking_usd'],
            f"Tariff ({import_costs['tariff_rate_percent']}%)": import_costs['tariff_amount_usd']}
        
        cost_df = pd.DataFrame([{'Cost Item': k, 'Amount ($)': v} for k, v in costs.items() if v > 0])
        fig2 = px.pie(cost_df, values='Amount ($)', names='Cost Item', title='Cost Distribution', hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)
        
        c1, c2 = st.columns(2)
        c1.metric("Total Import", f"${import_costs['total_import_cost_usd']:,.2f}")
        c2.metric("Per Unit", f"${import_costs['per_unit_import_cost_usd']:,.2f}")
        
        st.markdown("---")
        st.subheader("🏪 Marketplace Fees")
        
        if include_amazon:
            st.markdown("**Amazon FBA**")
            st.table(pd.DataFrame([
                {"Fee": "Referral", "Amount": f"${amazon_fba['referral_fee_usd']:.2f} ({amazon_fba['referral_fee_percent']}%)"},
                {"Fee": "Fulfillment", "Amount": f"${amazon_fba['fulfillment_fee_usd']:.2f}"},
                {"Fee": "Storage", "Amount": f"${amazon_fba['storage_fee_monthly_usd']:.2f}"},
                {"Fee": "Total/Unit", "Amount": f"${amazon_fba['per_unit_fees_usd']:.2f}"}
            ]))
        
        if include_walmart:
            st.markdown("**Walmart WFS**")
            st.table(pd.DataFrame([
                {"Fee": "Referral", "Amount": f"${walmart_wfs['referral_fee_usd']:.2f} ({walmart_wfs['referral_fee_percent']}%)"},
                {"Fee": "Fulfillment", "Amount": f"${walmart_wfs['fulfillment_fee_usd']:.2f}"},
                {"Fee": "Pick & Pack", "Amount": f"${walmart_wfs['pick_pack_fee_usd']:.2f}"},
                {"Fee": "Weight", "Amount": f"${walmart_wfs['weight_handling_usd']:.2f}"},
                {"Fee": "Total/Unit", "Amount": f"${walmart_wfs['per_unit_fees_usd']:.2f}"}
            ]))
        
        st.markdown("---")
        st.subheader("📈 Unit Economics")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Landed Cost/Unit", f"${total_cost:,.2f}")
        c2.metric("Selling Price", f"${selling_price:,.2f}")
        c3.metric("Gross Margin", f"${gross_margin:,.2f}")
        c4.metric("Margin %", f"{gross_margin_pct:.1f}%")
        
        st.download_button("📥 Download CSV", pd.DataFrame(st.session_state.items).to_csv(index=False), "container_order.csv", "text/csv")

st.markdown("---")
st.caption("Container Economics Calculator v1.0 | Import China to USA")
