TITLE = 'Logo TV'
PREFIX = '/video/logotv'
ART = 'art-default.jpg'
ICON = 'icon-default.png'

BASE_URL = 'http://www.logotv.com'
SHOWS = 'http://www.logotv.com/shows/'
VIDEOS = 'http://www.logotv.com/video/showall.jhtml'
PLAYLIST_URL = 'http://www.logotv.com/video/?id='
RE_EPISODE  = Regex('[-/]episode-(\d{1,3})[-/]')
RE_SEASON  = Regex('-season-(\d{1,2})-')
VIDEO_AJAX = BASE_URL + '/include/%s?id=%s&seasonId=%s&resultSize=30&template=/shows/platform/watch/modules/seasonRelatedPlaylists'
RE_EXX = Regex('/E(\d+)')

#SPECIAL_AJAX = 'http://www.logotv.com/global/music/tentpole/events_responsive_2.0/timeline/timeline.jhtml?config=%2Fevents%2F'
#SPECIAL_AJAX2 ='%2F2.0%2Fdata%2Ftimeline_config.jhtml&wrapper=false&howMany=40&tag=video'
####################################################################################################
# Set up containers for all possible objects
def Start():

    ObjectContainer.title1 = TITLE
    ObjectContainer.art = R(ART)

    DirectoryObject.thumb = R(ICON)
    EpisodeObject.thumb = R(ICON)
    VideoClipObject.thumb = R(ICON)

    # Since all functions would use a pull cache of one hour, just extablishing that here instead
    HTTP.CacheTime = CACHE_1HOUR 
 
#####################################################################################
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu():
    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(ProduceCarousels, title='Logo Shows', url=SHOWS), title='Logo Shows')) 
    oc.add(DirectoryObject(key=Callback(ProduceCarousels, title='Logo Videos', url=VIDEOS), title='Logo Videos')) 
    #To get the InputDirectoryObject to produce a search input in Roku, prompt value must start with the word "search"
    oc.add(SearchDirectoryObject(identifier="com.plexapp.plugins.logotv", title=L("Search Logo Videos"), prompt=L("Search for Videos")))
    return oc
#####################################################################################
# For Producing Sections for Video and Shows page
@route(PREFIX + '/producecarousels')
def ProduceCarousels(title, url):
    oc = ObjectContainer(title2=title)
    #THIS DATA PULL IS ALSO USED TWICE TOP PULL SHOW AND VIDEO SECTIONS
    data = HTML.ElementFromURL(url)
    for video in data.xpath('//div[@class="carousel_section_container"]'):
        show_type = video.xpath('.//@id')[0]
        # The video page has an extra h2 in code and must be put first or title comes up blank
        try:
            title = video.xpath('.//div[@class="carousel_section_title"]/h2//text()')[0].strip()
        except:
            title = video.xpath('.//div[@class="carousel_section_title"]//text()')[0]
        oc.add(DirectoryObject(key=Callback(MoreVideos, title=title, url=url, show_type=show_type), title = title))

    if url==SHOWS:
        oc.add(DirectoryObject(key=Callback(ProduceShows, title='All Logo Shows'), title='All Logo Shows')) 

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are sections to list right now.")
    else:
        return oc
#####################################################################################
# For Producing All Shows list at bottom of show page
@route(PREFIX + '/produceshows')
def ProduceShows(title):
    oc = ObjectContainer(title2=title)
    #THIS DATA PULL IS ALSO USED IN TWO OTHER PLACES FOR SHOWS
    data = HTML.ElementFromURL(SHOWS)
    for video in data.xpath('//div[@class="a_to_z_item"]/a'):
        url = video.xpath('.//@href')[0]
        if not url.startswith('http://'):
            url = BASE_URL + url
        # One series is hosted at another site so have to tell it to not include this series
        if not url.startswith('http://www.logotv.com'):
            continue
        title = video.xpath('.//text()')[0]
        if '/events/' in url:
            oc.add(DirectoryObject(key=Callback(SpecialVideos, title=title, url=url), title=title))
        else:
            if not url.endswith('series.jhtml'):
                if not url.endswith('/'):
                    url = url + '/'
                url = url + 'video/'
            oc.add(DirectoryObject(key=Callback(ShowSections, title=title, url=url), title=title))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no shows to list right now.")
    else:
        return oc
#########################################################################################
# This will produce the items in the carousel sections for shows and video page
@route(PREFIX + '/morevideos')
def MoreVideos(title, url, show_type):
    oc = ObjectContainer(title2=title)
    #THIS DATA PULL IS ALSO USED FOR SHOWS IN THE PRODUCESHOWS FUNCTION
    data = HTML.ElementFromURL(url)
    for video in data.xpath('//div[@id="carousel-%s"]//div/a' %show_type):
        vid_url = video.xpath('.//@href')[0]
        if vid_url.startswith('http://'):
            # One series is hosted at another site so have to tell it to not include this series
            if not vid_url.startswith('http://www.logotv.com'):
                continue
            else:
                pass
        else:
            vid_url = BASE_URL + vid_url
        title = video.xpath('./div[@class="title"]//text()')[0]
        thumb = video.xpath('.//img/@src')[0].split('?')[0]
        if not thumb.startswith('http://'):
            thumb = BASE_URL + thumb
      
        if '/events/' in vid_url:
            oc.add(DirectoryObject(key=Callback(SpecialVideos, title=title, url=vid_url), title=title))
        elif not '/video/' in vid_url:
            if not vid_url.endswith('series.jhtml'):
                if not vid_url.endswith('/'):
                    vid_url = vid_url + '/'
                vid_url = vid_url + 'video/'
            oc.add(DirectoryObject(key=Callback(ShowSections, title=title, url=vid_url, thumb=thumb), title=title, thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))
        else:
            date = Datetime.ParseDate(video.xpath('./div[@class="addedDate"]//text()')[0])
            if 'movies' in show_type:
                oc.add(VideoClipObject(url = vid_url, title = title, originally_available_at = date, thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))
            else:
                # All appear to have an episode but some do not have a season but put both in a try/except to prevent any issues
                try: episode = int(RE_EPISODE.search(vid_url).group(1))
                except: episode = 0
                try: season = int(RE_SEASON.search(vid_url).group(1))
                except: season = 0
                oc.add(EpisodeObject(url = vid_url, title = title, index = episode, season = season, originally_available_at = date, thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos or shows to list right now.")
    else:
        return oc
#######################################################################################
# This function produces seasons for shows with new format
@route(PREFIX + '/showseasons')
def ShowSeasons(title, url, thumb=''):
    oc = ObjectContainer(title2=title)
    try: html = HTML.ElementFromURL(url, cacheTime = CACHE_1HOUR)
    except: return ObjectContainer(header="Empty", message="The URL is invalid.")
    season_list = html.xpath('//span[@id="season-dropdown"]//li/a')
    for section in season_list:
        season_title = section.xpath('./span//text()')[0].strip().title()
        season = int(season_title.split()[1])
        season_id = section.xpath('./@data-id')[0]
        oc.add(DirectoryObject(key=Callback(ShowSections, title=season_title, thumb=thumb, url=url, season=season, season_id=season_id), title=season_title, thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))
            
    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no season." )
    else:
        return oc
#######################################################################################
# This function produces sections for show format
# Some that end with series.jhtml should not and it is impossible to tell prior to redirect,
# so we have to test the url in this function first
@route(PREFIX + '/showsections', season=int)
def ShowSections(title, url, season=0, season_id='', thumb=''):
    oc = ObjectContainer(title2=title)
    if url.endswith('series.jhtml'):
        bad_url = True
    else:
        bad_url = False
    try: html = HTML.ElementFromURL(url, cacheTime = CACHE_1HOUR)
    except: return ObjectContainer(header="Empty", message="The url is invalid.")
    if not thumb:
        try:
            thumb = html.xpath('//meta[@name="thumbnail"]/@content')[0].split('?')[0]
            if not thumb.startswith('http://'):
                thumb = BASE_URL + thumb
        except: thumb = R(ICON)
    if url.endswith('series.jhtml'):
        # First we check if the url ends with series.jhtml but should be the new format url
        # and change it to a good url
        try:
            video_url = BASE_URL + html.xpath('//ul[@class="nav"]/li//a[text()="Watch"]/@href')[0]
            url = video_url.split('full-episodes')[0]
            html = HTML.ElementFromURL(url, cacheTime = CACHE_1HOUR)
            bad_url = False
        # Otherwise we send it to the function to produce old format videos
        except:
            oc.add(DirectoryObject(key=Callback(ShowOldVideos, title="All Videos", url=url), title="All Videos", thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))
    if not bad_url:
        # if this is the first time thru then try to get the season id
        if season==0:
            try: season_id = html.xpath('//span[@id="season-dropdown"]//li[@class="active"]/a/@data-id')[0]
            except: season_id = None
        section_list = html.xpath('//span[@id="video-filters-dropdown"]//li/a')
        for section in section_list:
            section_url = section.xpath('./@href')[0]
            if not section_url.startswith('http://'):
                section_url = BASE_URL + section_url
            section_title = section.xpath('./span/text()')[0].title()
            id = section.xpath('./@data-seriesid')[0]
            # Add the filter for seasons ajax and assign ajax type for ones without series id
            if section_title=='Full Episodes':
                id = id + '&filter=fullEpisodes'
                ajax_type = 'series/relatedEpisodes'
            else:
                ajax_type = 'series/relatedPlaylists'
            #if there is a season_id, change the ajax type to seasons
            if season_id:
                ajax_type = 'shows/seasonAllVideosAjax'
            ajax_url = VIDEO_AJAX %(ajax_type, id, season_id)
            oc.add(DirectoryObject(key=Callback(ShowVideos, title=section_title, url=ajax_url, season=season), title=section_title, thumb=thumb))

    # If there are multiple season, add a directory listing for all seasons
    season_list = html.xpath('//span[@id="season-dropdown"]//li/a')
    if len(season_list)> 1 and season==0:
        oc.add(DirectoryObject(key=Callback(ShowSeasons, title="All Seasons", thumb=thumb, url=url), title="All Seasons", thumb = thumb))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="The show either has no videos or is in a format that is not currently supported." )
    else:
        return oc
#######################################################################################
# This function produces videos for the shows
# FOR NOW I HAVE CHOSEN TO NOT SHOW RESULTS THAT HAVE "NOT AVAILABLE" BUT INCLUDE THOSE THAT GIVE A DATE FOR WHEN IT WILL BE AVAILABLE
@route(PREFIX + '/showvideos', season=int, start=int)
def ShowVideos(title, url, season=0, start=0):

    oc = ObjectContainer(title2=title)
    count=0
    local_url = '%s&start=%s' %(url, start)
    try: data = HTML.ElementFromURL(local_url)
    except: return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    video_list = data.xpath('//div[contains(@class,"grid-item")]')
    for video in video_list:
        count = count+1
        try: vid_avail = video.xpath('.//div[@class="message"]//text()')[0]
        except: vid_avail = 'Now'
        if vid_avail == 'not available':
            continue
        vid_title = video.xpath('.//div[@class="header"]/span[@class="hide"]//text()')[0].strip()
        thumb = video.xpath('.//meta[@itemprop="thumbnailUrl"]/@content')[0].split('?')[0]
        try: seas_ep = video.xpath('.//div[@class="header"]/span[@itemprop="name"]//text()')[0].strip()
        except: seas_ep = ''
        if vid_avail == 'Now':
            vid_type = video.xpath('./@data-filter')[0]
            vid_url = video.xpath('.//meta[@itemprop="url"]/@content')[0]
            if not vid_url:
                continue
            if not vid_url.startswith('http://'):
                vid_url = BASE_URL + vid_url
            try: desc = video.xpath('.//div[@itemprop="description"]/span//text()')[0].strip()
            except: desc = ''
            try: duration = Datetime.MillisecondsFromString(duration = video.xpath('.//meta[@itemprop="duration"]/@content')[0].split('T')[1].split('S')[0])
            except: duration = 0
            date = Datetime.ParseDate(video.xpath('.//meta[@itemprop="uploadDate"]/@content')[0])
            try: episode = int(RE_EXX.search(seas_ep).group(1))
            except: episode = None

            oc.add(EpisodeObject(
                url = vid_url, 
                season = season,
                index = episode,
                title = vid_title, 
                thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON),
                originally_available_at = date,
                duration = duration,
                summary = desc
            ))
        else:
            avail_date = vid_avail.split()[1]
            avail_title = 'LOCKED UNTIL %s - %s' %(avail_date, vid_title)
            oc.add(PopupDirectoryObject(key=Callback(NotAvailable, avail=vid_avail), title=avail_title, thumb=thumb))
      
    if count==30:
        start=start+30
        oc.add(NextPageObject(key = Callback(ShowVideos, title=title, url=url, season=season, start=start), title = L("Next Page ...")))
      
    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos available to watch." )
    else:
        return oc
#################################################################################################################
# This function produces videos from the table layout used by old show video pages
# This function picks up all videos in all pages even without paging code
@route(PREFIX + '/showoldvideos')
def ShowOldVideos(title, url):
    oc = ObjectContainer(title2=title)
    try: data = HTML.ElementFromURL(url)
    except: return ObjectContainer(header=L('Error'), message=L('Unable to access data for this show. Webpage URL no longer valid'))
    for video in data.xpath('//ol[@id="olListing"]/li[@itemtype="http://schema.org/VideoObject"]'):
        title = video.xpath('./@maintitle')[0]
        content_type = video.xpath('.//li[@class="list-ct"]//text()')[0]
        thumb = video.xpath('./meta[@itemprop="thumbnail"]/@content')[0].split('?')[0]
        thumb = thumb.replace('70x53.jpg', '510x340.jpg')
        if not thumb:
            try: thumb = BASE_URL + video.xpath('.//*[@itemprop="thumbnail"]/@src')[0].split('?')[0]
            except: thumb = R(ICON)
        else:
            thumb = BASE_URL + thumb
        vid_url = BASE_URL + video.xpath('./@mainurl')[0]
        # need to add these videos to URL service
        if '/shows/' in vid_url:
            continue
        desc = video.xpath('./@maincontent')[0]
        try: date = Datetime.ParseDate(video.xpath('./@mainposted')[0])
        except: date = Datetime.Now()
        if content_type == 'Full Movies':
            # if movie or doc in url, no season or episode number, so create a movie object
            oc.add(MovieObject(url = vid_url, title = title, thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON),
                originally_available_at = date, summary = desc))
        else:
            episode = video.xpath('.//li[@class="list-ep"]//text()')[0]
            if episode.isdigit()==True:
                season = int(episode[0])
                episode = int(episode)

                oc.add(EpisodeObject(
                    url = vid_url, 
                    season = season,
                    index = episode,
                    title = title,
                    thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON),
                    originally_available_at = date,
                    summary = desc
                ))
            else:
                # Since video clips for Logo are usually playlist, we change these to playlist urls that are recognized by url service 
                if '#id=' in vid_url:
                    vid_id = vid_url.split('#id=')[1]
                    vid_url = PLAYLIST_URL + vid_id

                oc.add(VideoClipObject(
                    url = vid_url, 
                    title = title,
                    thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON),
                    originally_available_at = date,
                    summary = desc
                ))
    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    else:
        return oc
#######################################################################################
# This function produces videos for specials
# Only one has multiple pages so just showing first page of results for now
@route(PREFIX + '/specialvideos', sub=int, start=int)
def SpecialVideos(title, url, thumb='', start=0, sub=0):

    oc = ObjectContainer(title2=title)
    header_list=[]
    try: data = HTML.ElementFromURL(url + '/video.jhtml')
    except: return ObjectContainer(header="Empty", message="There are no videos to list right now.")

    # This creates a list for the all other shows in the first run through
    if sub==0:
        video_list = data.xpath('//div[contains(@class, "videoList group-1")]//div[contains(@class, "grid-item")]')
        # To pick up specials with a different format
        if not video_list:
            video_list = data.xpath('//div[contains(@class, "item group video")]')
        header_list = data.xpath('//div[contains(@class, "videoList group")]//header/span')
        # Get the main player video
        try:
            vid_thumb = data.xpath('//div[@id="mainPlayer"]//div[@class="imgDefered"]/@data-src')[0]
            oc.add(VideoClipObject(
                url = BASE_URL + data.xpath('//div[@id="mainPlayer"]/a/@href')[0], 
                title = data.xpath('//div[@id="mainPlayer"]//div[@class="header"]/span//text()')[0], 
                thumb = Resource.ContentsOfURLWithFallback(url=vid_thumb, fallback=ICON)
            ))
        except: pass
    # This creates a list for those header titles
    elif sub==1:
        video_list = data.xpath('//header/span[text()="%s"]/ancestor::div[contains(@class, "video-list")]//div[contains(@class, "grid-item")]' %title)
    # This creates a list for the alt special pages
    else:
        video_list = data.xpath('//div[contains(@class, "item group video")]')
        
    # The try is for alt special pages, the excepts are for all others
    for video in video_list:
        try:
            vid_mgid = video.xpath('.//span/@data-content-uri')[0]
            vid_url = PLAYLIST_URL + vid_mgid.split('logotv.com:')[1].split('/')[0]
        except: vid_url = BASE_URL + video.xpath('.//a/@href')[0]
        vid_thumb = video.xpath('.//div[@class="imgDefered"]/@data-src')[0]
        try: vid_title = video.xpath('.//div[@class="header"]/span/span//text()')[0].strip()
        except: vid_title = video.xpath('.//div[@class="header"]//span//text()')[0].strip()
        try: vid_desc = video.xpath('.//div[@class="deck"]/span[@class="fullText"]//text()')[0].strip()
        except: vid_desc = ''
        try:date = Datetime.ParseDate(video.xpath('.//div[@class="meta muted"]/small//text()')[0])
        except: date = Datetime.Now()
        oc.add(VideoClipObject(
            url = vid_url, 
            title = vid_title, 
            thumb = Resource.ContentsOfURLWithFallback(url=vid_thumb, fallback=ICON),
            originally_available_at = date,
            summary = vid_desc
        ))
      
    # Gets the header title for other videos and then sends it back 
    if header_list:
        if not thumb:
            thumb = BASE_URL + data.xpath('//meta[@name="thumbnail"]/@content')[0].replace('140x105', '281x211')
        for header in header_list:
            header_title = header.xpath('.//text()')[0]
            oc.add(DirectoryObject(key=Callback(SpecialVideos, title=header_title, url=url, sub=1), title=header_title, thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos available to watch." )
    else:
        return oc
############################################################################################################################
# This function creates an error message for entries that are not currently available
@route(PREFIX + '/notavailable')
def NotAvailable(avail):
  return ObjectContainer(header="Not Available", message='This video is currently unavailable - %s.' %avail)
