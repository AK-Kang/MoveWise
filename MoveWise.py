#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MoveWise.py
Purpose: 
    This py file performs exploratory data analysis of the 
    merged data file and present the visualization on a 
    streamlit-GUI dashboard. Users will be able to select 
    from the sidebar and the map to see statistics for 
    different states. They can also compare the living and 
    employment statisitics between two states and facilitate 
    their decision on relocations.
    
Python Group C2
    @author 1: Anni Kang;          andrew id: annik
    @author 2: Harshita Agrawal;   andrew id: hagrawa2
    @author 3: Yingyuan Lin;       andrew id: yingyual
    @author 4: Zheyu Yan;          andrew id: zheyuyan
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import seaborn as sns

# set the title and subtitle for the dashboard
APP_TITLE = "MoveWise"
APP_SUB_TITLE = 'Everything you need to know before relocating for jobs'

# create a sidebar for users to filter data by state
def display_state_filter(df, state_name):
    state_list = [''] + list(df['State'].unique())
    state_list.sort()
    # if no state manually selected, the state displayed by default will be Alabama (index 1)
    state_index = state_list.index(state_name) if state_name and state_name in state_list else 1
    return st.sidebar.selectbox('Select your State', state_list, state_index)

# create a sidebar for users to filter data by industry type
def display_industry_type_filter():
    return st.sidebar.radio('Industry Type', ['Management', 'Business', 'CS'])

# display an US map on the dashboard
def display_map(df):
    # restrict map to center on the United States
    map = folium.Map(location=[38, -96.5], zoom_start=4, scrollWheelZoom=False, tiles='CartoDB positron')
    
    # import geojson to create boarder for each state
    choropleth = folium.Choropleth(
        geo_data='us-state-boundaries.geojson',
        data=df,
        columns=('State', 'Index'),
        key_on='feature.properties.name',
        line_opacity=0.8,
        highlight=True
    )
    choropleth.geojson.add_to(map)

    # display name, living cost, and median home price for each state with mouse hover
    df_indexed = df.set_index('State')
    for feature in choropleth.geojson.data['features']:
        state_name = feature['properties']['name']
        feature['properties']['living_cost'] = 'Cost of Living: ' + '{:,}'.format(df_indexed.loc[state_name, 'Index'][0]) if state_name in list(df_indexed.index) else ''
        feature['properties']['median_home_price'] = 'Median Home Price: ' + '${:,}'.format(df_indexed.loc[state_name, 'Median Home Price'][0]) if state_name in list(df_indexed.index) else ''
        
    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(['name', 'living_cost', 'median_home_price'], labels=False)
        )
    
    # set map size
    st_map = st_folium(map, width=700, height=450)

    # a state will be returned after users click on that state
    state_name = ''
    if st_map['last_active_drawing']:
        state_name = st_map['last_active_drawing']['properties']['name']
    return state_name

# display the cost of living index by state and industry type as a metric
def display_living_index(df, state_name, industry_type):
    if state_name:
        df = df[(df['State'] == state_name) & (df['Industry'] == industry_type)]
        living_ind = df['Index']
        st.metric("Cost of Living index ", living_ind)
       
# display the median home price of selected state as a metric  
def display_median_home_price(df, state_name, industry_type, string_format = '${:,}'):
    if state_name:
        df = df[(df['State'] == state_name) & (df['Industry'] == industry_type)]
        med_home_price = df['Median Home Price'].values[0]
        st.metric("Median Home Price ", string_format.format(med_home_price))
  
# display the annual mean wage of selected state and industry type as a metric     
def display_annual_mean_wage(df, state_name, industry_type, string_format = '${:,}'):
    if state_name:
        df = df[(df['State'] == state_name) & (df['Industry'] == industry_type)]
        annual_mean_wage = df['Annual Mean Wage'].values[0]
        st.metric("Annual Mean Wage ", string_format.format(annual_mean_wage))

# plot various living statistics by state
def plot_state_living_cost_summary(df, state):
    state_data = df[df['State'] == state]
    state_melted = pd.melt(state_data, id_vars=['State'], value_vars=[
                           'Index', 'Grocery', 'Housing', 'Utilities', 'Transportation', 'Health', 'Misc.'])
    plt.figure(figsize=(6, 4))
    state_melted["value"] = state_melted["value"].astype(float)
    sns.barplot(data=state_melted, x='variable', y='value', alpha=0.8)
    plt.title(f'Living cost summary for {state}')
    plt.ylabel('Value')
    plt.xlabel('Metrics')
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(plt)

# compare living statistics and median rent price between two states
def comparison_between_state(df, state1, state2):
    selected_state = df[df['State'].isin([state1, state2])]
    state_melted = pd.melt(selected_state, id_vars=['State'], value_vars=[
        'Index', 'Grocery', 'Housing', 'Utilities', 'Transportation', 'Health', 'Misc.'])
    state_melted["value"] = state_melted["value"].astype(float)
    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(10, 10))
    sns.barplot(data=selected_state, x='State', y='Median Rent',
                ax=axes[0], alpha=0.8)
    axes[0].set_title(f'Median Rent Comparison Between {state1} and {state2}')
    plot = sns.barplot(data=state_melted, x='State', y='value', hue='variable',
                      ax=axes[1], alpha=0.8)
    axes[1].set_title(
        f'Living Cost Comparison Between {state1} and {state2}')
    plot.legend(loc='upper left', bbox_to_anchor=(1, 1), ncol=1)
    plt.ylabel('Value')
    plt.xlabel('Metrics')
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(plt)

# plot a box plot of the distribution 
def plot_distribution(df, attributes):
    # height in inches for each subplot
    height_per_plot = 4  
    fig, axes = plt.subplots(nrows=len(attributes) - 1, ncols=1, figsize=(10, height_per_plot * (len(attributes) - 1)))
    # Enumerate through both index (counter) and value (attribute)
    for counter, attribute in enumerate(attributes[:-1]):  
        df[attribute] = df[attribute].astype(float)
        sns.boxplot(df[attribute], ax=axes[counter])
        axes[counter].set_title(f'Distribution of {attribute}')
        # Identify outliers
        Q1 = df[attribute].quantile(0.25)
        Q3 = df[attribute].quantile(0.75)
        IQR = Q3 - Q1
        outliers = df[(df[attribute] < (Q1 - 1.5 * IQR)) | (df[attribute] > (Q3 + 1.5 * IQR))]
        for index, row in outliers.iterrows():
            axes[counter].text(0.3, row[attribute], row['State'], ha='center')
    plt.tight_layout()
    st.pyplot(plt)

# compute and display the difference in employment statistics between two states
def display_states_job_comparison(df, state1, state2, job):
    
    # return employment statistics by state and industry type
    def display_job_metrics(df, state, job):
        state_data = df[df['State'] == state]
        state_job_data = state_data[state_data['Industry'] == job]
        state_melted = pd.melt(state_job_data, id_vars=['State'], value_vars=[
            'Employment', 'Median Hourly Wage', 'Mean Hourly Wage', 'Annual Mean Wage'])
        employment_stats = str(int(state_melted["value"][0]))
        median_hw_stats = str(state_melted["value"][1])
        mean_hw_stats = str(state_melted["value"][2])
        annual_mw_stats = str(state_melted["value"][3])
        return employment_stats, median_hw_stats, mean_hw_stats, annual_mw_stats

    # retrieve data for two different states
    employment_stats1, median_hw_stats1, mean_hw_stats1, annual_mw_stats1 = display_job_metrics(df, state1, job)
    employment_stats2, median_hw_stats2, mean_hw_stats2, annual_mw_stats2 = display_job_metrics(df, state2, job)
    # display the statistics
    employment_diff = str(int(employment_stats2) - int(employment_stats1))
    median_hw_diff = str("{:.1f}".format(float(median_hw_stats2) - float(median_hw_stats1)))
    mean_hw_diff = str("{:.1f}".format(float(mean_hw_stats2) - float(mean_hw_stats1)))
    annual_mw_diff = str("{:.1f}".format(float(annual_mw_stats2) - float(annual_mw_stats1)))
    col1, col2 = st.columns(2)
    with col1:
        if float(employment_diff) >= 0:
            st.metric("Increase in Employment After the Move", employment_diff)
        if float(employment_diff) < 0:
            st.metric("Decrease in Employment After the Move", str(abs(int(employment_diff))))
        if float(mean_hw_diff) >= 0:
            st.metric("Increase in Mean Hourly Wage After the Move", mean_hw_diff)
        if float(mean_hw_diff) < 0:
            st.metric("Decrease in Mean Hourly Wage After the Move", str(abs(float(mean_hw_diff))))
    with col2:
        if float(median_hw_diff) >= 0:
            st.metric("Increase in Median Hourly Wage After the Move", median_hw_diff)
        if float(median_hw_diff) < 0:
            st.metric("Decrease in Median Hourly Wage After the Move", str(abs(float(median_hw_diff))))
        if float(annual_mw_diff) >= 0:
            st.metric("Increase in Annual Mean Wage After the Move", annual_mw_diff)
        if float(annual_mw_diff) < 0:
            st.metric("Decrease in Annual Mean Wage After the Move", str(abs(float(annual_mw_diff))))

# compare the cost of living index between two states
def display_states_index_comparison(df, state1, state2, job):
    # return statistics by state
    def get_index_value(df, state, job):
        state_data = df[(df['State'] == state) & (df['Industry'] == job)]
        if not state_data.empty:
            return state_data['Index'].values[0]
        return None
    # display statistics
    index1 = get_index_value(df, state1, job)
    index2 = get_index_value(df, state2, job)
    if index1 is not None and index2 is not None:
        index_diff = str("{:.1f}".format(index2 - index1))
        if float(index_diff) >= 0:
            st.metric("Increase in Cost of Living Index After the Move", index_diff)
        else:
            st.metric("Decrease in Cost of Living Index After the Move", str(abs(float(index_diff))))
    else:
        st.warning("Data not available for one or both selected states and industry.")

# compare the median home price statistics between two states  
def display_states_mhp_comparison(df, state1, state2, job):
    state_data1 = df[df['State'] == state1]
    state_job_data1 = state_data1[state_data1['Industry'] == job]
    state_melted1 = pd.melt(state_job_data1, id_vars=['State'], value_vars=[
                            'Median Rent', 'Rental Vacancy', 'Occupied Housing Units', 'Median Home Price'])
    state_data2 = df[df['State'] == state2]
    state_job_data2 = state_data2[state_data2['Industry'] == job]
    state_melted2 = pd.melt(state_job_data2, id_vars=['State'], value_vars=[
                            'Median Rent', 'Rental Vacancy', 'Occupied Housing Units', 'Median Home Price'])
    mhp_diff = str("{:.1f}".format(float(state_melted2['value'][3]) - float(state_melted1['value'][3])))
    if float(mhp_diff) >= 0:
        st.metric("Increase in Median Home Price After the Move", mhp_diff)
    if float(mhp_diff) < 0:
        st.metric("Decrease in Median Home Price After the Move", str(abs(float(mhp_diff))))
 
# create a barplot that displays the difference in statistics between two states    
def comparision_between_state(df, state1, state2):
    selected_state = df[df['State'].isin([state1, state2])]
    state_melted = pd.melt(selected_state, id_vars= ['State'], value_vars = [ 
    'Index', 'Grocery', 'Housing',
    'Utilities', 'Transportation', 'Health', 'Misc.'])
    state_melted["value"] = state_melted["value"].astype(float)
    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(10, 10))
    sns.barplot(data = selected_state, x='State', y='Median Rent', ax=axes[0], alpha = 0.8)
    axes[0].set_title(f'Median Rent Comparison Between {state1} and {state2}')
    plot = sns.barplot(data = state_melted, x='State', y='value', hue = 'variable', ax = axes[1], alpha = 0.8)
    axes[1].set_title(f'Living Cost Comparision Between {state1} and {state2}')
    plot.legend(loc='upper left', bbox_to_anchor=(1,1), ncol=1)
    plt.ylabel('Value')
    plt.xlabel('Metrics')
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(plt)
    
# display the employment statistics by state and industry type
def display_state_job_summary(df, state, job):
    if state:
        state_data = df[df['State'] == state]
        state_job_data = state_data[state_data['Industry'] == job]
        state_melted = pd.melt(state_job_data, id_vars= ['State'], value_vars = [ 
        'Employment', 'Median Hourly Wage', 'Mean Hourly Wage',
        'Annual Mean Wage'])
        employment_stats = str(int(state_melted["value"][0]))
        median_hw_stats = str(state_melted["value"][1])
        mean_hw_stats = str(state_melted["value"][2])
        annual_mw_stats = str(state_melted["value"][3])
        
        job_data = df[df['Industry'] == job]
        rank_employment_df = job_data.sort_values('Employment')
        rank_employment_df = rank_employment_df.reset_index()
        rank_employment_df = rank_employment_df.drop(columns = "index")
        rank_employment_df = rank_employment_df[rank_employment_df['State'] == state]
        rank_employment = str(51 - int(rank_employment_df.index.tolist()[0]))

        rank_MedianHW_df = job_data.sort_values('Mean Hourly Wage')
        rank_MedianHW_df = rank_MedianHW_df.reset_index()
        rank_MedianHW_df = rank_MedianHW_df.drop(columns = "index")
        rank_MedianHW_df = rank_MedianHW_df[rank_MedianHW_df['State'] == state]
        rank_MedianHW = str(51 - int(rank_MedianHW_df.index.tolist()[0]))
        
        rank_MeanHW_df = job_data.sort_values('Median Hourly Wage')
        rank_MeanHW_df = rank_MeanHW_df.reset_index()
        rank_MeanHW_df = rank_MeanHW_df.drop(columns = "index")
        rank_MeanHW_df = rank_MeanHW_df[rank_MeanHW_df['State'] == state]
        rank_MeanHW = str(51 - int(rank_MeanHW_df.index.tolist()[0]))

        rank_Annual_MW_df = job_data.sort_values('Median Hourly Wage')
        rank_Annual_MW_df = rank_Annual_MW_df.reset_index()
        rank_Annual_MW_df = rank_Annual_MW_df.drop(columns = "index")
        rank_Annual_MW_df = rank_Annual_MW_df[rank_Annual_MW_df['State'] == state]
        rank_Annual_MW = str(51 - int(rank_Annual_MW_df.index.tolist()[0]))
        
        col1, col2, col3, col4= st.columns(4)
        with col1:
            st.metric("Employment", employment_stats,"Rank in all states: " + rank_employment)
        with col2:
            st.metric("Median Hourly Wage($)", median_hw_stats,"Rank in all states: " + rank_MedianHW)
        with col3:
            st.metric("Mean Hourly Wage($)", mean_hw_stats,"Rank in all states: " + rank_MeanHW)
        with col4:
            st.metric("Annual Mean Wage($)", annual_mw_stats,"Rank in all states: " + rank_Annual_MW)



def main():
    st.set_page_config(APP_TITLE, layout = "wide")
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)
    
    #load data
    data = pd.read_csv("merged_data.csv")
    living_housing_info = data.drop(columns = ['Industry','Employment', 'Median Hourly Wage', 'Mean Hourly Wage', 'Annual Mean Wage'])
    living_housing_info = living_housing_info.drop_duplicates()
    living_housing_info = living_housing_info.reset_index()
    living_housing_info = living_housing_info.drop(columns= ["index"])

    tabs = st.sidebar.radio("Choose a Tab", ["Overview", "State Information", "State Comparison"])

    # Tab 1: Overview
    if tabs == "Overview":
        attributes = ['Index', 'Grocery', 'Housing','Utilities', 'Transportation', 'Health', 'Misc.']
        st.header("Overview")
        display_map(data)
        st.subheader("Cost of Living Distribution")
        plot_distribution(living_housing_info, attributes)
    

    # Tab 2: State Information
    elif tabs == "State Information":
        st.header("State Information")
        state_name = display_map(data)
        state_name = display_state_filter(data, state_name)
        industry_type = display_industry_type_filter()
        st.subheader(f'{state_name} Facts')
        col1, col2 = st.columns(2)
        with col1:
            display_living_index(data, state_name, industry_type)
        with col2:
            display_median_home_price(data, state_name, industry_type)
        

        st.subheader(f'{state_name} {industry_type} Employment & Salary Info')
        display_state_job_summary(data, state_name, industry_type)

        st.subheader(f'{state_name} Living Cost Summary')
        plot_state_living_cost_summary(living_housing_info, state_name)
            

    # Tab 3: Comparison 
    elif tabs == "State Comparison":
        st.header("State Comparison")
        state1 = st.sidebar.selectbox( "Select Your Current State:", data["State"].unique(), key = "option3")
        state2 = st.sidebar.selectbox( "Select the State You Want to Move to:", data["State"].unique(), key = "option4")
        industry_type = st.sidebar.radio("Select the Industry:", data["Industry"].unique())
        st.subheader(f'If You Move to {state2} From {state1}')
        st.subheader(f'{industry_type} Employment & Salary Info')
        display_states_job_comparison(data, state1, state2, industry_type)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader('Housing Info')
            display_states_mhp_comparison(data, state1, state2, industry_type)
        with col2:    
            st.subheader('Cost of Living Info')
            display_states_index_comparison(data, state1, state2, industry_type)
        comparision_between_state(data, state1, state2)


if __name__ == "__main__": 
    main()
