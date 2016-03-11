TITLE = 'Logo TV'
PREFIX = '/video/logotv'
ART = 'art-default.jpg'
ICON = 'icon-default.png'

BASE_URL = 'http://www.logotv.com'
MANIFEST_URL = BASE_URL + '/feeds/triforce/manifest/v5?url=%s&currentManifest=Production'
MOSTVIEWED = BASE_URL + '/feeds/ent_m177_logo/V1_0_2/db369f93-463b-4181-b1ef-9bcb9ef6b781'

SECTION_LIST = [("All Episodes", '/episode-guide'), ("Video Clips", '/video-guide')]
SKIP_ZONES = ('header', 'footer', 'ads-reporting')
RE_MANIFEST = Regex('var triforceManifestFeed = (.+?);', Regex.DOTALL)
####################################################################################################
# Set up containers for all possible objects
def Start():

    ObjectContainer.title1 = TITLE
    ObjectContainer.art = R(ART)

    DirectoryObject.thumb = R(ICON)
    EpisodeObject.thumb = R(ICON)
    VideoClipObject.thumb = R(ICON)

    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'

#####################################################################################
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu():
    oc = ObjectContainer()

    oc.add(DirectoryObject(key=Callback(AllMenu, title='Shows', url=BASE_URL+'/shows'), title='Shows'))
    oc.add(DirectoryObject(key=Callback(VideoSections, title='Full Episodes', url=BASE_URL+'/full-episodes'), title='Full Episodes'))
    oc.add(DirectoryObject(key=Callback(ShowVideos, title='Most Viewed Videos', url=MOSTVIEWED), title='Most Viewed Videos'))
    return oc
####################################################################################################
# Function to find all the zones in a page's json and create a section for them
# This function will only return those with a title for the feed and items or shows
@route(PREFIX + '/allmenu')
def AllMenu(title, url):

    oc = ObjectContainer()
    feed_list = GetJSONFeeds(url)
    if not feed_list:
        return ObjectContainer(header="Incompatible", message="Unable to find feeds for %s." %url)

    for (title, feed_url, feed_type) in feed_list:
        if feed_type=='shows':
            oc.add(DirectoryObject(key=Callback(ProduceShows, title=title, url=feed_url), title=title))
        else:
            oc.add(DirectoryObject(key=Callback(ShowVideos, title=title, url=feed_url), title=title))

    return oc
#####################################################################################
# For Producing show results from json
# This includes the Featured and A to Z from show main page
@route(PREFIX + '/produceshows')
def ProduceShows(title, url, alpha=''):

    oc = ObjectContainer(title2=title)
    json = JSON.ObjectFromURL(url)

    if not alpha:
        try:
            alpha_test = json['result']['shows']['hash']
            show_list = []
        except:
            try: show_list = json['result']['shows']
            # Add an exception here in case there are no show results
            except: return ObjectContainer(header="Empty", message="This page is not in the proper format to return shows." )
    else:
        show_list = json['result']['shows'][alpha]

    if show_list or alpha:
        for show in show_list:
            try: url = show['canonicalURL']
            except: url = show['url']
            title = show['title']
            title = title.replace('&#36;', '$')
            try: thumb = show['images'][0]['url']
            except: thumb = ''
            oc.add(DirectoryObject(
                key=Callback(ShowSections, title=title, thumb=thumb, url=url),
                title=title,
                thumb = Resource.ContentsOfURLWithFallback(url=thumb)
            ))

    else:
        for alpha in json['result']['shows']:
            if alpha=='hash':
                alpha_title = '#'
            else:
                alpha_title = alpha.title()
            oc.add(DirectoryObject(
                key=Callback(ProduceShows, title=alpha_title, url=url, alpha=alpha),
                title=alpha_title
            ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no shows to list right now.")
    else:
        return oc
#######################################################################################
# This function produces video clip and full episode sections for shows
@route(PREFIX + '/showsections')
def ShowSections(title, url, thumb=''):

    oc = ObjectContainer(title2=title)
    if not thumb:
        try: thumb = HTML.ElementFromURL(url, cacheTime = CACHE_1DAY).xpath('//meta[@property="og:image"]/@content')[0].strip()
        except: thumb = ''
    # Get the full episode and video clip feeds
    for (section_title, section) in SECTION_LIST:
        feed_url = GetJSONFeeds(url + section, section_title)
        if feed_url:
            json = JSON.ObjectFromURL(feed_url)
            videos = json['result']['items']
            try: filters = json['result']['filters']
            except: filters = []
            if videos:
                # Check the length of filters to see if it needs to go to the VideoSections() function
                # Full Episodes are not returned, since it is a shorter list of All Episodes, so those must have more than 2 filters
                if ('Episode' in section_title and len(filters)>2) or ('Video' in section_title and len(filters)>1):
                    oc.add(DirectoryObject(
                        key=Callback(VideoSections, title=section_title, url=feed_url, thumb=thumb),
                        title=section_title,
                        thumb = Resource.ContentsOfURLWithFallback(url=thumb)
                    ))
                else:
                    oc.add(DirectoryObject(
                        key=Callback(ShowVideos, title=section_title, url=feed_url),
                        title=section_title,
                        thumb = Resource.ContentsOfURLWithFallback(url=thumb)
                    ))
        else:
            Log('This section url is incompatible - %s' %(url + section))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no video sections for this show." )
    else:
        return oc
#######################################################################################
# This function produces sections from the pull down menu within a page
# For shows it is a pull down for seasons but other pages may list other options like a list of show full episode pages
@route(PREFIX + '/videosections')
def VideoSections(title, url, thumb=''):

    oc = ObjectContainer(title2=title)
    if '/feeds/ent_'in url:
        feed_url = url
    else:
        feed_url = GetJSONFeeds(url, title)

    if not feed_url:
        return ObjectContainer(header="Incompatible", message="Unable to find feed for %s." %url)

    json = JSON.ObjectFromURL(feed_url)

    # Find pull-down sections
    try: pulldown_list = json['result']['filters']
    except:
        # Create a listing for all Videos
        oc.add(DirectoryObject(key=Callback(ShowVideos, title='All %s' %title, url=feed_url),
            title = 'All %s' %title
        ))
        # FOR MTV, VH1, AND LOGOTV. SPIKE AND CC SINCE HAVE FULL EPISODE BY SHOW LIST ON NAVIGATION
        #pulldown_list = []
        # Check for a show pull down list instead of filters
        try: pulldown_list = json['result']['shows']
        except: pulldown_list = []

    for vid_type in pulldown_list:
        try:
            type_title = vid_type['name']
            # Full Episodes and Watch Episodes the same as All Episodes without specials, so skip
            if 'full episodes' in type_title.lower() or 'watch episodes' in type_title.lower():
                continue
        except: type_title = vid_type['title']
        type_url = vid_type['url']
        oc.add(DirectoryObject(
            key=Callback(ShowVideos, title=type_title, url=type_url),
            title=type_title,
            thumb=Resource.ContentsOfURLWithFallback(url=thumb)
        ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos to list." )
    else:
        return oc
#######################################################################################
# This function produces the videos listed in json under items
@route(PREFIX + '/showvideos')
def ShowVideos(title, url):

    oc = ObjectContainer(title2=title)
    json = JSON.ObjectFromURL(url)
    try: videos = json['result']['items']
    except:
        try: videos = json['result']['episodes']
        except:
            try: videos = json['result']['playlist']['videos']
            except: return ObjectContainer(header="Empty", message="There are no videos to list right now.")

    for video in videos:
        # VIDEOS ARE ALL UNLOCKED
        vid_url = findEpisodePlayer(video['url'])
        # Found a couple urls where with '/episodes/' that are not in URL pattern, so skip them
        if vid_url.startswith(BASE_URL + '/episodes/'):
            continue
        try: thumb=video['images'][0]['url']
        except: thumb = ''
        try: episode = int(video['season']['episodeNumber'])
        except: episode = 0
        try: season = int(video['season']['seasonNumber'])
        except: season = 0
        try: show = video['show']['title']
        except: show = ''
        # Found some that do not have an airdate
        try: unix_date = video['airDate']
        except:
            try: unix_date = video['publishDate']
            except: unix_date = None
        if unix_date:
            date = Datetime.FromTimestamp(float(unix_date)).strftime('%m/%d/%Y')
            date = Datetime.ParseDate(date)
        else:
            date = Datetime.Now()
        # Durations for clips have decimal points
        duration = video['duration']
        if not duration:
            duration = 0
        if not isinstance(duration, int):
            if '.' in duration:
               duration = duration.split('.')[0]
            try: duration = int(duration)
            except: duration = 0
        duration = duration * 1000

        if show:
            oc.add(EpisodeObject(
                url = vid_url,
                show = show,
                season = season,
                index = episode,
                title = video['title'],
                thumb = Resource.ContentsOfURLWithFallback(url=thumb ),
                originally_available_at = date,
                duration = duration,
                summary = video['description']
            ))
        else:
            oc.add(VideoClipObject(
                url = vid_url,
                title = video['title'],
                thumb = Resource.ContentsOfURLWithFallback(url=thumb ),
                originally_available_at = date,
                duration = duration,
                summary = video['description']
            ))

    try: next_page = json['result']['nextPageURL']
    except: next_page = None
    if next_page:
        oc.add(NextPageObject(
            key = Callback(ShowVideos, title=title, url=next_page),
            title = L("Next Page ...")
        ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no unlocked videos available to watch." )
    else:
        return oc
####################################################################################################
# Function to pull all the zone feed urls and titles except header and footer and those without a title
@route(PREFIX + '/getjsonfeeds')
def GetJSONFeeds(url, title=''):

    json_feed = ''
    feed_list = []
    try: zone_list = JSON.ObjectFromURL(MANIFEST_URL %url, cacheTime = CACHE_1DAY)['manifest']['zones']
    except:
        try:
            content = HTTP.Request(url, cacheTime=CACHE_1DAY).content
            manifest_data = RE_MANIFEST.search(content).group(1)
            zone_list = JSON.ObjectFromString(manifest_data)['manifest']['zones']
        except: zone_list = []

    for zone in zone_list:
        if zone not in SKIP_ZONES:
            json_feed = zone_list[zone]['feed']
            json = JSON.ObjectFromURL(json_feed, cacheTime = CACHE_1DAY)
            try: feed_name = json['result']['promo']['headline']
            except:
                try: feed_name = json['result']['promotion']['headline']
                except:
                    try: feed_name = json['result']['playlist']['shortTitle']
                    except: feed_name = ''
            if feed_name:
                feed_name = feed_name.title()
                if title:
                    if title in feed_name:
                        Log('the value of json_feed is %s' %json_feed)
                        return json_feed
                        break
                else:
                    type_list = ['items', 'episodes', 'playlist', 'shows']
                    for result in json['result']:
                        item_list = json['result'][result]
                        # Only return those with items or shows section in results
                        if result in type_list and item_list:
                            json_info = (feed_name, json_feed, result)
                            feed_list.append(json_info)
                            break

    if title:
        Log('the value of json_feed is %s' %json_feed)
        return json_feed
    else:
        Log('the value of feed_list is %s' %feed_list)
        return feed_list

def findEpisodePlayer(pageUrl):
    Log("pageUrl: " + pageUrl)
    req = HTTP.Request(pageUrl, values=None, headers={}, cacheTime=CACHE_INTERVAL, encoding=None, errors=None, timeout=5000, immediate=False, sleep=0, data=None)
    #Log("content: " + req.content)
    content = req.content
    mgid = re.search('mgid:arc:episode[^"]+', content).group(0)
    config_url = 'http://media.mtvnservices.com/pmt-arc/e1/players/mgid:arc:episode:logotv.com:/context1/context2/context7/config.xml?uri={0}&type=network&ref=www.logotv.com&geo=US&group=music&network=cable&device=Other&networkConnectionType=None'.format(mgid)
    config_url = urllib.quote(config_url)
    flash_link = 'http://media.mtvnservices.com/player/prime/mediaplayerprime.2.10.16.swf?uri={0}&type=network&ref=www.logotv.com&geo=US&group=music&network=cable&device=Other&networkConnectionType=None&CONFIG_URL={1}'.format(mgid, config_url)
    Log("flash link: " + flash_link)
    return flash_link
