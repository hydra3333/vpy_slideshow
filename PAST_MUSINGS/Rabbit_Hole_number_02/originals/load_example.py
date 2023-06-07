import load
my_loader = load.Sources(d2vwitch_dir='F:\\tools', ffmsindex_dir='F:\\tools')
dataclasses = my_loader.get_data(['video2.mkv','video2.mpg']
for data in dataclasses
    clip = data.clip
    if data.load_isError:
        log = data.load_log
        #clip was not loaded, can read the log,  abort
    # work with clip here
