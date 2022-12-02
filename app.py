import streamlit as st
import pandas as pd
import numpy as np

st.title('Rooming Auditor')

mothership_file = st.file_uploader("Select mothership CSV file to upload")
rooming_report_file = st.file_uploader("Select rooming report CSV file to upload")

if mothership_file is not None and rooming_report_file is not None:
    import numpy as np
    import pandas as pd
    import re

    # Read CSV files
    ms = pd.read_csv(mothership_file)
    rr = pd.read_csv(rooming_report_file)

    # Clean up room type and guest data in mothership dataframe
    ms["room type"].replace(to_replace='({")(.*)("})', value='\\2', regex=True, inplace=True)
    ms["guests"].replace(to_replace='"', value='', regex=True, inplace=True)
    ms["guests"].replace(to_replace='({)(.*)(})', value='\\2', regex=True, inplace=True)
    ms["guests"] = ms["group leader first"] + " " + ms["group leader last"] + "," + ms["guests"]
    ms["guests"] = ms["guests"].fillna(ms["group leader first"] + " " + ms["group leader last"])
    ms["guests"].replace(to_replace=', ', value=',', regex=False, inplace=True)
    ms["guests"] = ms["guests"].str.lower()
    ms["ms_guest_list"] = ms["guests"].str.split(',')
    ms['ms_guest_list'] = ms['ms_guest_list'].apply(lambda row: sorted(set(row)))

    # Add additional rows for each mothership dataframe row with multiple rooms
    ms_to_add = ms[ms["n_rooms"] == 6].copy()
    ms_to_add.loc[:, ("n_rooms")] -= 1
    ms = pd.concat([ms, ms_to_add])
    ms_to_add = ms[ms["n_rooms"] == 5].copy()
    ms_to_add.loc[:, ("n_rooms")] -= 1
    ms = pd.concat([ms, ms_to_add])
    ms_to_add = ms[ms["n_rooms"] == 4].copy()
    ms_to_add.loc[:, ("n_rooms")] -= 1
    ms = pd.concat([ms, ms_to_add])
    ms_to_add = ms[ms["n_rooms"] == 3].copy()
    ms_to_add.loc[:, ("n_rooms")] -= 1
    ms = pd.concat([ms, ms_to_add])
    ms_to_add = ms[ms["n_rooms"] == 2].copy()
    ms_to_add.loc[:, ("n_rooms")] -= 1
    ms = pd.concat([ms, ms_to_add])
        
    # Clean up guest data in rooming report dataframe
    rr["Guest #1 Name"] = rr["Guest #1 Name"].fillna("").str.strip()
    rr["Guest #2 Name"] = rr["Guest #2 Name"].fillna("").str.strip()
    rr["Guest #3 Name"] = rr["Guest #3 Name"].fillna("").str.strip()
    rr["Guest #4 Name"] = rr["Guest #4 Name"].fillna("").str.strip()
    rr["Guest #5 Name"] = rr["Guest #5 Name"].fillna("").str.strip()
    rr["Guest #6 Name"] = rr["Guest #6 Name"].fillna("").str.strip()
    rr["rrguests"] = rr[["Guest #1 Name", "Guest #2 Name", "Guest #3 Name", "Guest #4 Name", "Guest #5 Name", "Guest #6 Name"]].agg(','.join, axis=1)
    rr["rrguests"].replace(to_replace=',*$', value='', regex=True, inplace=True)
    rr["rrguests"].replace(to_replace=', ', value=',', regex=False, inplace=True)
    rr["rrguests"] = rr["rrguests"].str.lower()

    rrguest_df = rr.groupby("Order Number")["rrguests"].apply(','.join).reset_index()
    rrguest_df = rrguest_df.rename(columns={'rrguests':'rrguests_grouped'})
    rr = rr.merge(rrguest_df, how='left', on='Order Number')
    rr["rr_guest_list"] = rr["rrguests_grouped"].str.split(',')
    rr['rr_guest_list'] = rr['rr_guest_list'].apply(lambda row: sorted(set(row)))

    # Update mothership dataframe indices and create summary dataframe
    ms["order_room_number"] = ms["order_number"] + "_" + ms["n_rooms"].astype(str)
    ms = ms.set_index(['order_room_number'])
    ms_count = ms.groupby("order_room_number")["event"].count()

    # Update rooming report dataframe indices and create summary dataframe
    rr["order_room_number"] = rr["Order Number"] + "_" + rr["# of rooms"].astype(str)
    rr = rr.set_index(["order_room_number"])
    rr_count = rr.groupby("order_room_number")["Package"].count()

    # Update summary dataframe column names and compare for rows that appear in one dataframe but not the other
    ms_count_check = pd.merge(ms_count, rr_count, how="left", on="order_room_number")
    ms_count_check = ms_count_check.rename(columns={'event':'ms_count', 'Package':'rr_count'})
    ms_count_check['compare'] = np.where((ms_count_check['ms_count'] != ms_count_check['rr_count']) | (ms_count_check['rr_count'].isnull()), 1, 0)
    matched_rows = ms_count_check[ms_count_check['compare'] == 0]

    rr_count_check = pd.merge(ms_count, rr_count, how="right", on="order_room_number")
    rr_count_check = rr_count_check.rename(columns={'event':'ms_count', 'Package':'rr_count'})
    rr_count_check['compare'] = np.where((rr_count_check['ms_count'] != rr_count_check['rr_count']) | (rr_count_check['rr_count'].isnull()), 1, 0)

    unmatched_ms = ms_count_check[ms_count_check['compare'] == 1]
    unmatched_ms = unmatched_ms.rename(columns={"compare": "room_count_in_mothership_different_from_rooming"})
    unmatched_ms = unmatched_ms.merge(ms, how='left', on='order_room_number')
    unmatched_ms = unmatched_ms.rename(columns={"order_number": "order_no", "n_rooms": "room_no", "hotel": "ms_hotel", "room type": "ms_room_type", "checkin_date": "ms_checkin", "checkout_date": "ms_checkout"})
    unmatched_ms = unmatched_ms[["order_no", "room_no", "ms_hotel", "ms_room_type", "ms_checkin", "ms_checkout", "ms_guest_list","room_count_in_mothership_different_from_rooming"]]

    unmatched_rr = rr_count_check[rr_count_check['compare'] == 1]
    unmatched_rr = unmatched_rr.rename(columns={"compare": "room_count_in_rooming_different_from_mothership"})
    unmatched_rr = unmatched_rr.merge(rr, how='left', on='order_room_number')
    unmatched_rr = unmatched_rr.rename(columns={"Order Number": "order_no", "# of rooms": "room_no", "Hotel": "rr_hotel", "Room Type": "rr_room_type", "Check In": "rr_checkin", "Check Out": "rr_checkout"})
    unmatched_rr = unmatched_rr[["order_no", "room_no", "rr_hotel", "rr_room_type", "rr_checkin", "rr_checkout", "rr_guest_list","room_count_in_rooming_different_from_mothership"]]

    # Process data from each dataframe and consolidate to hotel, room type, checkin date, checkout date, guest list columns to compare
    matched_rows = matched_rows.merge(ms, how='inner', on="order_room_number")
    matched_rows = matched_rows[["hotel", "room type", "checkin_date", "checkout_date", "ms_guest_list"]]
    matched_rows = matched_rows.rename(columns={"hotel": "ms_hotel", "room type": "ms_room_type", "checkin_date": "ms_checkin", "checkout_date": "ms_checkout"})

    matched_rows = matched_rows.merge(rr, how='inner', on='order_room_number')
    matched_rows = matched_rows.rename(columns={"Order Number": "order_no", "# of rooms": "room_no", "Hotel": "rr_hotel", "Room Type": "rr_room_type", "Check In": "rr_checkin", "Check Out": "rr_checkout"})
    matched_rows = matched_rows[["order_no", "room_no", "ms_hotel", "rr_hotel", "ms_room_type", "rr_room_type", "ms_checkin", "rr_checkin", "ms_checkout", "rr_checkout", "ms_guest_list", "rr_guest_list"]]

    # Identify mismatching data for rows that appear in both dataframes
    matched_rows['hotel_mismatch'] = np.where((matched_rows['ms_hotel'] != matched_rows['rr_hotel']), 1, 0)
    matched_rows['room_type_mismatch'] = np.where((matched_rows['ms_room_type'] != matched_rows['rr_room_type']), 1, 0)
    matched_rows['checkin_mismatch'] = np.where((matched_rows['ms_checkin'] != matched_rows['rr_checkin']), 1, 0)
    matched_rows['checkout_mismatch'] = np.where((matched_rows['ms_checkout'] != matched_rows['rr_checkout']), 1, 0)
    matched_rows['guest_mismatch'] = np.where((matched_rows['ms_guest_list'] != matched_rows['rr_guest_list']), 1, 0)
    data_mismatches = matched_rows[(matched_rows['hotel_mismatch'] == 1) | (matched_rows['room_type_mismatch'] == 1) | (matched_rows['checkin_mismatch'] == 1) | (matched_rows['checkout_mismatch'] == 1) | (matched_rows['guest_mismatch'] == 1)]

    export_df = pd.concat([data_mismatches, unmatched_ms, unmatched_rr])

    with open('export_csv.csv','w') as f:
        export_df.to_csv(f)
    with open('export_csv.csv') as f:
        st.download_button(
            label='Download Processed File', 
            data=f, 
            file_name='rooming_audit.csv',
            mime='text/csv'
        )