#!/usr/bin/env python
# coding: utf-8

# In[40]:


import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import seaborn as sns
import glob
from scipy import stats
from bokeh.plotting import figure, show, output_notebook
from bokeh.models import HoverTool
import plotly.express as px


# In[3]:


# load data
file_paths = glob.glob("C:/Users/Hassan/Desktop/divvy-tripdata/*.csv")
# Load all CSV files into a list of DataFrames
dfs = [pd.read_csv(file) for file in file_paths]

# Concatenate all DataFrames into one
combined_df = pd.concat(dfs, ignore_index=True)


# ### Data Discovering

# In[4]:


combined_df.head(10)


# In[5]:


combined_df.info()


# In[6]:


combined_df.describe()


# In[7]:


combined_df.size


# In[8]:


combined_df.shape


# ### Data Cleaning

# In[9]:


# Check for missing values
missing_values = combined_df.isnull().sum()
print("Missing values:\n", missing_values)


# In[10]:


# Impute missing values for latitude and longitude columns with median
combined_df['end_lat'].fillna(combined_df['end_lat'].median(), inplace=True)
combined_df['end_lng'].fillna(combined_df['end_lng'].median(), inplace=True)

# Remove rows with missing station-related information
combined_df.dropna(subset=['start_station_name', 'start_station_id', 'end_station_name', 'end_station_id'], inplace=True)


# In[11]:


# Check for missing values in station-related columns after removal
missing_station_values = combined_df[['start_station_name', 'start_station_id', 'end_station_name', 'end_station_id']].isnull().sum()
print("Missing values in station-related columns after removal:\n", missing_station_values)


# In[15]:


# Convert timestamp columns to datetime format
combined_df['started_at'] = pd.to_datetime(combined_df['started_at'])
combined_df['ended_at'] = pd.to_datetime(combined_df['ended_at'])

# Check consistency in data types and formats
print(combined_df.dtypes)

# Detect and handle outliers

z_scores = stats.zscore(combined_df['start_lat'])
outliers1 = combined_df[(z_scores > 3) | (z_scores < -3)]


# verify
print(combined_df.head())


# In[16]:


# Standardize station names (convert to lowercase and remove leading/trailing whitespaces)
combined_df['start_station_name'] = combined_df['start_station_name'].str.lower().str.strip()
combined_df['end_station_name'] = combined_df['end_station_name'].str.lower().str.strip()


# In[17]:


# Check for duplicate rows
duplicate_rows = combined_df[combined_df.duplicated()]

# Display duplicate rows
print("Duplicate Rows:")
print(duplicate_rows)


# In[18]:


# creating columns
combined_df['month'] = combined_df['started_at'].dt.month_name().str.slice(stop=3)
combined_df['year'] = combined_df['started_at'].dt.year.astype(str)
combined_df['day_of_week'] = combined_df['started_at'].dt.day_name().str.slice(stop=3)
combined_df['hour'] = combined_df['started_at'].dt.strftime('%I%p')


# ride duration in minutes
combined_df['ride_duration'] = (combined_df['ended_at'] - combined_df['started_at']).dt.total_seconds() / 60

# Ordering day_of_week column
combined_df['day_of_week'] = pd.Categorical(combined_df['day_of_week'], ordered=True)

# Ordering month column
combined_df['month'] = pd.Categorical(combined_df['month'], ordered=True)

# Renaming columns
combined_df.rename(columns={'rideable_type': 'bike', 'member_casual': 'user'}, inplace=True)

# Remove rows where ride duration is negative
combined_df = combined_df[combined_df['ride_duration'] >= 0]

combined_df.head()


# In[19]:


combined_df['ride_duration'].describe()


# In[20]:


# pivot table for the heatmap
pivot_table = combined_df.pivot_table(index='day_of_week', columns='hour', values='ride_id', aggfunc='count')

# Ordering the days of the week for the heatmap
day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
pivot_table = pivot_table.reindex(day_order)

# Plotting heatmap
plt.figure(figsize=(12, 8))
sns.heatmap(pivot_table, cmap='coolwarm', linewidths=.5, annot=True, fmt="d")
plt.title('Heatmap of Rides by Hour and Day of the Week')
plt.xlabel('Hour of the Day')
plt.ylabel('Day of the Week')
plt.show()


# In[23]:


# average ride duration by month
monthly_avg_duration = combined_df.groupby('month')['ride_duration'].mean()

# Plotting trends
plt.figure(figsize=(18, 6))

monthly_avg_duration.plot(kind='bar', color='skyblue')
plt.title('Average Ride Duration by Month')
plt.xlabel('Month')
plt.ylabel('Average Ride Duration (minutes)')


plt.tight_layout()
plt.show()


# In[24]:


# Group by user and bike
grouped_df = combined_df.groupby(['user', 'bike'])

# aggregate statistics for ride duration
ride_duration_stats = grouped_df['ride_duration'].agg(['mean', 'median', 'std', 'min', 'max'])

# statistics
print(ride_duration_stats)


# In[26]:


# Defining bins for ride duration categories
bins = [0, 10, 30, float('inf')]
labels = ['Short', 'Medium', 'Long']

# Apply pd.cut() to categorize ride durations
combined_df['duration_category'] = pd.cut(combined_df['ride_duration'], bins=bins, labels=labels, right=False)

# Group by user and bike and count the number of rides in each category
grouped_df = combined_df.groupby(['user', 'bike', 'duration_category'], observed=True).size().unstack(fill_value=0)

# percentage for each category
grouped_df_percentage = grouped_df.div(grouped_df.sum(axis=1), axis=0) * 100

# percentage distribution
grouped_df_percentage.plot(kind='bar', stacked=True, figsize=(10, 6))
plt.title('Percentage of Ride Durations by User and Rider')
plt.xlabel('User and Rider')
plt.ylabel('Percentage')
plt.legend(title='Duration Category')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()


# In[27]:


# number of rides for each user type
user_type_counts = combined_df['user'].value_counts()

# percentage of casual vs. member riders
user_type_percentage = user_type_counts / user_type_counts.sum() * 100

print("Percentage of Casual vs. Member Riders:")
print(user_type_percentage)


# In[28]:


# Group by month and count the number of rides
monthly_rides = combined_df.groupby(combined_df['started_at'].dt.month)['ride_id'].count()

# number of rides per month
monthly_rides.plot(kind='bar', figsize=(10, 6))
plt.title('Number of Rides by Month')
plt.xlabel('Month')
plt.ylabel('Number of Rides')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()


# In[29]:


# Group by day of the week and count the number of rides
daily_rides = combined_df.groupby(combined_df['started_at'].dt.day_name())['ride_id'].count()

# number of rides per day of the week
daily_rides.plot(kind='bar', figsize=(10, 6))
plt.title('Number of Rides by Day of the Week')
plt.xlabel('Day of the Week')
plt.ylabel('Number of Rides')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()


# In[30]:


# Group by month and user type, and calculate the average ride duration
monthly_duration = combined_df.groupby(['month', 'user'])['ride_duration'].mean()

# average ride duration by month and user type
monthly_duration.unstack().plot(kind='bar', figsize=(10, 6))
plt.title('Average Ride Duration by Month and User Type')
plt.xlabel('Month')
plt.ylabel('Average Ride Duration (minutes)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()


# In[31]:


# Group by day of the week and user type, and calculate the average ride duration
daily_duration = combined_df.groupby(['day_of_week', 'user'])['ride_duration'].mean()

# average ride duration by day of the week and user type
daily_duration.unstack().plot(kind='bar', figsize=(10, 6))
plt.title('Average Ride Duration by Day of the Week and User Type')
plt.xlabel('Day of the Week')
plt.ylabel('Average Ride Duration (minutes)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()


# In[32]:


# Group by user type and bike type, and count the number of rides
bike_type_usage = combined_df.groupby(['user', 'bike'])['ride_id'].count()

# bike type usage by user type
bike_type_usage.unstack().plot(kind='bar', figsize=(10, 6))
plt.title('Bike Type Usage by User Type')
plt.xlabel('User Type')
plt.ylabel('Number of Rides')
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()


# In[39]:


combined_df['month_year'] = combined_df['started_at'].dt.to_period('M') 
monthly_rides = combined_df.groupby('month_year')['ride_id'].count()


output_notebook()

p = figure(title="Monthly Ride Trends", x_axis_label='Month and Year', y_axis_label='Number of Rides',
           x_axis_type='datetime', width=800)

p.line(x=monthly_rides.index.to_timestamp(), y=monthly_rides.values, legend_label='Total Rides')
p.add_tools(HoverTool())

show(p)



# In[48]:


# Group data by user type and calculate average duration and other metrics
user_grouped = combined_df.groupby('user')['ride_duration'].agg(['mean', 'std', 'count'])

print(user_grouped)

# a t-test to test if the differences are statistically significant

casual_durations = combined_df[combined_df['user'] == 'casual']['ride_duration']
member_durations = combined_df[combined_df['user'] == 'member']['ride_duration']

t_stat, p_val = ttest_ind(casual_durations, member_durations, equal_var=False)
print(f"T-statistic: {t_stat}, P-value: {p_val}")


# In[ ]:




