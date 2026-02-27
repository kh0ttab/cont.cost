# ... existing code ...
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
    
    used_volume = sum(item['volume_cuft'] * item['quantity'] for item in items)
    used_weight = sum(item['weight_lbs'] * item['quantity'] for item in items)
    
    total_items = sum(item['quantity'] for item in items)
    
    return {
        'total_items': total_items,
        'space_utilization_percent': round((used_volume / max_volume_cuft) * 100, 2),
        'weight_utilization_percent': round((used_weight / max_weight_lbs) * 100, 2),
        'remaining_volume_cuft': round(max_volume_cuft - used_volume, 2),
        'total_weight_lbs': round(used_weight, 2),
        'max_weight_lbs': max_weight_lbs
    }

def calculate_import_costs(items, china_warehouse_days=7, total_ocean_freight=5000.0, inland_trucking=1200.0):
    fees_data = load_fees_data()
    import_fees = fees_data['import_fees']
    shipping_costs = fees_data['shipping_costs']
    tariff_rates = fees_data['tariff_rates']
    
    total_units = sum(item['quantity'] for item in items)
    total_cost = sum(item['unit_cost_usd'] * item['quantity'] for item in items)
    total_volume = sum(item['volume_cuft'] * item['quantity'] for item in items)
    
    ocean_freight_cost = total_ocean_freight
    chinese_warehousing = total_volume * shipping_costs['chinese_warehousing_per_day_per_cuft'] * china_warehouse_days
    insurance = (total_cost + ocean_freight_cost) * shipping_costs['insurance_rate']
    
    mpf = (total_cost + ocean_freight_cost) * import_fees['merchandise_processing_fee']
    hmf = (total_cost + ocean_freight_cost) * import_fees['harbor_maintenance_fee']
    isf = (total_cost + ocean_freight_cost) * import_fees['import_security_fee']
    port_to_warehouse = (total_volume / 35.315) * 150 # Convert cuft to cbm
    
    # Calculate tariff based on the weighted mix of items in the container
    tariff_amount = 0
    for item in items:
        item_fraction = (item['volume_cuft'] * item['quantity']) / total_volume if total_volume > 0 else 0
        item_cif = (item['unit_cost_usd'] * item['quantity']) + (ocean_freight_cost * item_fraction) + (insurance * (item['unit_cost_usd'] * item['quantity'] / total_cost if total_cost > 0 else 0))
        category = item['product_category'].lower()
        tariff_rate = tariff_rates['categories'].get(category, tariff_rates['default'])
        tariff_amount += item_cif * (tariff_rate / 100)
    
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
        'isi_fee_usd': import_fees['isi_fee'],
        'merchandise_processing_usd': round(mpf, 2),
        'harbor_maintenance_usd': round(hmf, 2),
        'import_security_usd': round(isf, 2),
        'port_to_warehouse_usd': round(port_to_warehouse, 2),
        'inland_trucking_usd': inland_trucking,
        'tariff_amount_usd': round(tariff_amount, 2),
        'total_import_cost_usd': round(total_import, 2),
        'per_unit_import_cost_usd': round(total_import / total_units, 2) if total_units > 0 else 0
    }

def calculate_amazon_fba(item, selling_price):
# ... existing code ...
with st.sidebar:
    st.header("⚙️ Configuration")
    container_type = st.selectbox("Container Type", ["20ft", "40ft", "40hc"], index=2)
    utilization_target = st.slider("Target Utilization %", 50, 100, 90) / 100
    china_warehouse_days = st.number_input("China Warehouse (days)", 0, 90, 7)
    ocean_freight = st.number_input("Total Ocean Freight ($)", 100.0, 50000.0, 5000.0, 100.0)
    inland_trucking = st.number_input("Inland Trucking ($)", 500.0, 3000.0, 1200.0, 100.0)
    include_amazon = st.checkbox("Amazon FBA Fees", value=True)
    include_walmart = st.checkbox("Walmart WFS Fees", value=True)

st.subheader("📋 Add Items")
# ... existing code ...
if st.session_state.items and st.button("🚀 Calculate", type="primary", use_container_width=True):
    fees_data = load_fees_data()
    max_vol = fees_data['containers'][container_type]['volume_cuft']
    space_needed = sum(i['volume_cuft'] * i['quantity'] for i in st.session_state.items)
    
    if space_needed > max_vol:
        st.error(f"❌ Exceeds container! Need {space_needed:.0f} cu ft, max {max_vol} cu ft")
    else:
        item = st.session_state.items[0]
        container_result = calculate_container_fit(st.session_state.items, container_type, utilization_target)
        import_costs = calculate_import_costs(st.session_state.items, china_warehouse_days, ocean_freight, inland_trucking)
        selling_price = item['unit_cost_usd'] * 3
        
        amazon_fba = {}
        walmart_wfs = {}
        if include_amazon: amazon_fba = calculate_amazon_fba(item, selling_price)
        if include_walmart: walmart_wfs = calculate_walmart_wfs(item, selling_price)
        
        total_cost = import_costs['per_unit_import_cost_usd']
        if include_amazon: total_cost += amazon_fba.get('per_unit_fees_usd', 0)
        suggested_price = total_cost / 0.7
        gross_margin = selling_price - total_cost
        gross_margin_pct = (gross_margin / selling_price * 100) if selling_price > 0 else 0
        
        st.success("✅ Calculation Complete!")
        st.markdown("---")
        st.subheader("📊 Container Space Analysis")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Items in Order", f"{container_result['total_items']}")
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
            'Tariffs': import_costs['tariff_amount_usd']}
        
        cost_df = pd.DataFrame([{'Cost Item': k, 'Amount ($)': v} for k, v in costs.items() if v > 0])
        fig2 = px.pie(cost_df, values='Amount ($)', names='Cost Item', title='Cost Distribution', hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)
        
        c1, c2 = st.columns(2)
        c1.metric("Total Import", f"${import_costs['total_import_cost_usd']:,.2f}")
        c2.metric("Avg Per Unit", f"${import_costs['per_unit_import_cost_usd']:,.2f}")
        
        st.markdown("---")
        st.subheader("🏪 Marketplace Fees")
# ... existing code ...
