# Patchy 
Track you working hours within csv files and print a status

## Usage
`patchy.py -p` to patch in/out
`patchy.py` to check status

## Output
Status will be printed as:
`<Hours worked today> (<Hours left for todays pensum), <total over-/undertime`
Output will be color encoded:
- Red if the CSV is not correct (You actually cant over a daychange)
- Yellow if todays pensum is not reached and you are not patched in
- Green if you are patched in and worked enough
- Light green if you are patched in and did not yet reach this days pensum
- White if you reached the pensum and are not patched in.

## Storage
Files are stored in ~/.patchy.

There are two types of files:
### balance.csv
This CSV contains aggregated hours for every past month.
The current month is not calculated until next month.
### yyyy_m.csv
Monthly patchings. Each line is a `patch-in, patch-out, diff` entry of this month.
Once the next month is reached, the past months data is aggregated and written into balance.csv
