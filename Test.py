import pandas as pd
import numpy as np
from datetime import datetime
from datetime import timedelta
from ast import literal_eval
import seaborn as sns
import matplotlib.pyplot as plt


def extraction_plot(data, x, y, hue, title):
    sns.set()
    plt.figure(figsize=(10, 4))
    graph = sns.barplot(x=x, y=y, hue=hue, data=data)
    sns.despine(left=True, right=True)
    graph.set_yscale('log')
    graph.set_yticks([], minor=True)
    graph.set_yticklabels([])
    graph.set_ylabel('')
    graph.set_xlabel('')
    graph.legend(loc='upper right')
    graph.set_title(title)
    for b in graph.patches:
        height = b.get_height()
        if height > 0.0:
            graph.text(b.get_x() + (b.get_width()/8), height, round(height, 4), fontsize=8)
    plt.savefig('C:\\Users\\User\PycharmProjects\Wikr_test\Output_data\\' + title + '.png', dpi=120, quality=90)
    # plt.show()
    plt.close()
    return graph


palette = ['#f4d498', '#51ba93', '#f4d1da', '#3f7d90', '#ecf6b4']
sns.set_palette(palette, 5)

# Input data
dimensions_table = pd.read_csv('C:\\Users\\User\PycharmProjects\Wikr_test\Input_data\posts_list.csv', sep='\t')
fact_table = pd.read_csv('C:\\Users\\User\PycharmProjects\Wikr_test\Input_data\posts_insights.csv', sep='\t')

# Output file
output_file = pd.ExcelWriter('C:\\Users\\User\PycharmProjects\Wikr_test\Output_data\Output_file.xlsx',
                             engine='xlsxwriter')

# Posts by type quantity (p.1)
posts_by_types = pd.pivot_table(dimensions_table, values='id', index='type_of_post', aggfunc='count')
posts_by_types.sort_values('id', ascending=False, inplace=True)

# Posts by types (p.2)
dimensions_table['created_datetime'] = dimensions_table['created_datetime'].apply(
    lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
dimensions_table['created_datetime_day'] = dimensions_table['created_datetime'].apply(
    lambda x: datetime.strftime(x, '%Y-%m-%d'))
fact_table['update_time'] = fact_table['update_time'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))

posts_types_by_days = pd.pivot_table(dimensions_table, values='id', index=['created_datetime_day', 'type_of_post'],
                                     aggfunc='count')
posts_types_by_days = posts_types_by_days.reset_index().sort_values(['created_datetime_day', 'id'],
                                                                    ascending=[1, 0]).set_index(['created_datetime_day',
                                                                                                'type_of_post'])
posts_types_by_days.reset_index(inplace=True)
posts_types_by_days.to_excel(output_file, sheet_name='Posts by types over days',
                             header=['Day', 'Type of post', 'Quantity'],
                             index=False)

plt.figure(figsize=(12, 5))
posts_types_graph = sns.barplot(x='created_datetime_day', y='id', hue='type_of_post',
                                data=posts_types_by_days.reset_index())
sns.despine(left=True, right=True)
posts_types_graph.set_ylabel('')
posts_types_graph.set_xlabel('Days')
posts_types_graph.set_yticks([])
posts_types_graph.set_yticklabels([])
posts_types_graph.legend(title='Type of post', loc='upper right')
for b in posts_types_graph.patches:
    height = b.get_height()
    posts_types_graph.text(b.get_x() + (b.get_width()/4), height+1, int(height), fontsize=10)
posts_types_graph.set_title('Posts by types over days')
plt.savefig('C:\\Users\\User\PycharmProjects\Wikr_test\Output_data\Posts by types over days.png', dpi=120,
            quality=90)
# plt.show()
plt.close()

# Join dimension_table with fact_table (p.3)
joined_table = pd.merge(dimensions_table, fact_table, how='inner', left_on='id', right_on='post_id')

# Define post_impressions_unique by days(p.4)
impressions_data = pd.DataFrame()
for post in joined_table['id'].unique():
    tmp = joined_table.loc[joined_table['id'] == post].copy()
    create_time = tmp['created_datetime'].tolist()[0]
    hour_10th = create_time + timedelta(hours=10)
    hour_11th = create_time + timedelta(hours=11)
    analyze_time = [x for x in tmp['update_time'] if (x > hour_10th) and (x <= hour_11th)]
    post_insights = tmp.loc[tmp['update_time'].isin(analyze_time)]
    impressions_data = impressions_data.append(post_insights)

impressions_data['post_consumptions_by_type_unique'] = impressions_data['post_consumptions_by_type_unique'].apply(
    lambda x: literal_eval(x))
impressions_by_type = pd.pivot_table(impressions_data, values='post_impressions_unique',
                                     index=['created_datetime_day', 'type_of_post'],
                                     aggfunc=['sum', 'min', 'max', np.mean])

impressions_by_type.to_excel(output_file, sheet_name='Post_impressions_unique by days')

# Extraction сoefficient (p.5)
impressions_data['link_clicks'] = impressions_data['post_consumptions_by_type_unique'].apply(lambda x: x['link clicks'])
impressions_data['extr_сoef'] = impressions_data['link_clicks'] / impressions_data['post_impressions_unique']

extraction_by_type = pd.pivot_table(impressions_data, values='extr_сoef',
                                    index=['created_datetime_day', 'type_of_post'],
                                    aggfunc=['min', 'max', np.mean])

extraction_by_type.to_excel(output_file, sheet_name='Extraction_coefficient')

min_extr_by_type = extraction_by_type[('min', 'extr_сoef')].reset_index()
min_extr_by_type.columns = ['Day', 'Type of post', 'Min extr_coef']
min_extr_graph = extraction_plot(min_extr_by_type, 'Day', 'Min extr_coef', 'Type of post',
                                 'Min extraction coefficient over days')

max_extr_by_type = extraction_by_type[('max', 'extr_сoef')].reset_index()
max_extr_by_type.columns = ['Day', 'Type of post', 'Max extr_coef']
max_extr_graph = extraction_plot(max_extr_by_type, 'Day', 'Max extr_coef', 'Type of post',
                                 'Max extraction coefficient over days')

avg_extr_by_type = extraction_by_type[('mean', 'extr_сoef')].reset_index()
avg_extr_by_type.columns = ['Day', 'Type of post', 'Avg extr_coef']
avg_extr_graph = extraction_plot(avg_extr_by_type, 'Day', 'Avg extr_coef', 'Type of post',
                                 'Avg extraction coefficient over days')

# Top-5 posts by likes daily
own_link_posts = joined_table.loc[((joined_table['caption'] == 'mambee.com') |
                                  (joined_table['caption'] == 'fabiosa.guru')) &
                                  (joined_table['type_of_post'] == 'link')].copy()

own_link_posts['post_stories_by_action_type'] = own_link_posts['post_stories_by_action_type'].apply(
    lambda x: literal_eval(x))

own_link_posts['likes_qty'] = [d['like'] if 'like' in d else 0 for d in own_link_posts['post_stories_by_action_type']]

plt.figure(figsize=(12, 5))
n = 1
for day in own_link_posts['created_datetime_day'].unique():
    own_link_posts_daily = own_link_posts.loc[own_link_posts['created_datetime_day'] == day].copy()
    own_link_posts_top = pd.DataFrame()
    for post in own_link_posts_daily['id'].unique():
        post_likes = own_link_posts_daily.loc[(own_link_posts_daily['id'] == post), 'likes_qty'].max()
        own_link_posts_top = own_link_posts_top.append(own_link_posts_daily.loc[
                                                           own_link_posts_daily['likes_qty'] == post_likes])
    own_link_posts_top = own_link_posts_top.nlargest(5, 'likes_qty')
    own_link_posts_top = own_link_posts_top.sort_values(by='likes_qty', ascending=False)
    own_link_posts_top[['post_id', 'likes_qty']].to_excel(output_file, sheet_name=day)

    plt.subplot(2, 3, n)
    tmp_graph = sns.barplot(x='name', y='likes_qty', data=own_link_posts_top)
    sns.despine(left=True, right=True)
    tmp_graph.set_yticks([], minor=True)
    tmp_graph.set_yticklabels([])
    tmp_graph.set_ylabel('')
    tmp_graph.set_xlabel('')
    tmp_graph.set_xticklabels(range(1, 6))
    tmp_graph.set_title(day)
    for b in tmp_graph.patches:
        height = b.get_height()
        if height > 0.0:
            tmp_graph.text(b.get_x() + (b.get_width()/4), height, int(height), fontsize=8)
    n += 1
plt.tight_layout()
plt.savefig('C:\\Users\\User\PycharmProjects\Wikr_test\Output_data\Top_posts_by_days.png', dpi=120, quality=90)
# plt.show()

output_file.save()
output_file.close()
