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
ALL_VID_AJAX = 'http://www.logotv.com/include/shows/seasonAllVideosAjax?id=%s&seasonId=%s&resultSize=1000&template=/shows/platform/watch/modules/seasonRelatedPlaylists&start=0'
FULL_EP_AJAX = 'http://www.logotv.com/shows/seasonAllVideosAjax?device=desktop&id=%s&seasonId=%s&filter=fullEpisodes&template=/shows/platform/watch/modules/seasonRelatedPlaylists'
SPECIAL_AJAX = 'http://www.logotv.com/global/music/tentpole/events_responsive_2.0/timeline/timeline.jhtml?config=%2Fevents%2F'
SPECIAL_AJAX2 ='%2F2.0%2Fdata%2Ftimeline_config.jhtml&wrapper=false&howMany=40&tag=video'
RE_EXX = Regex('/E(\d+)')

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
        return ObjectContainer(header="Empty", message="There are shows to list right now.")
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
            oc.add(DirectoryObject(key=Callback(ShowSeasons, title=title, url=url), title=title))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are shows to list right now.")
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
            oc.add(DirectoryObject(key=Callback(SpecialVideos, title=title, url=vid_url), title=title, thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))
        elif not '/video/' in vid_url:
            oc.add(DirectoryObject(key=Callback(ShowSeasons, title=title, url=vid_url, thumb=thumb), title=title, thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))
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
        return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    else:
        return oc
#######################################################################################
# This function produces seasons for shows
@route(PREFIX + '/showseasons')
def ShowSeasons(title, url, thumb=''):
    oc = ObjectContainer(title2=title)
    # Some that end in series.jhtml still use the old table to list videos but some resolve to  
    # the new format. So first we remove series.jhtml from all urls and see if the request works
    if url.endswith('series.jhtml'):
        url = url.split('series.jhtml')[0]
    # Found one that give an error because it does not end with a slash
    if not url.endswith('/'):
        url = url + '/'
    local_url = url + 'video/'
    try: html = HTML.ElementFromURL(local_url, cacheTime = CACHE_1HOUR)
    except: html = None

    if html:
        new_season_list = html.xpath('//span[@id="season-dropdown"]//li/a')
        if not thumb:
            try: thumb = BASE_URL + html.xpath('//meta[@name="thumbnail"]/@content')[0]
            except: thumb = R(ICON)
        if len(new_season_list)> 0:
            for section in new_season_list:
                title = section.xpath('./span//text()')[0].strip().title()
                season = int(title.split()[1])
                season_id = section.xpath('./@data-id')[0]
                oc.add(DirectoryObject(key=Callback(ShowSections, title=title, thumb=thumb, url=local_url, season=season, season_id=season_id), title=title, thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))
        else:
            # COULD GET THE SEASON FROM THE FIRST VIDEO HERE WITH REGEX IF THE SEASON WAS WANTED
            oc.add(DirectoryObject(key=Callback(ShowSections, title='Current Season', thumb=thumb, url=local_url, season=0), title='Current Season', thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))

    # Those that still use the old table format will go to a 404 page, so we 
    # add back the series.jhtml and send those to the old table format video function
    else:
        oc.add(DirectoryObject(key=Callback(ShowVideosOld, title="All Videos", url=url + "series.jhtml"), title="All Videos", thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos listed for this show.")
    else:
        return oc
#######################################################################################
# This function produces sections for shows
@route(PREFIX + '/showsections', season=int)
def ShowSections(title, thumb, url, season, season_id=''):
    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(url, cacheTime = CACHE_1HOUR)
    section_list = html.xpath('//span[@id="video-filters-dropdown"]//li/a')
    for section in section_list:
        id = section.xpath('./@data-seriesid')[0]
        url = BASE_URL + section.xpath('./@href')[0]
        section_title = section.xpath('./span/text()')[0].title()
        if season_id:
            if 'Full Episodes' in section_title:
                section_url = FULL_EP_AJAX %(id, season_id)
            else:
                section_url = ALL_VID_AJAX %(id, season_id)
        else:
            section_url = url
        oc.add(DirectoryObject(key=Callback(ShowVideos, title=section_title, url=section_url, season=season), title=section_title, thumb=thumb))
    return oc
#######################################################################################
# This function produces videos for shows
# LIMITING RESULTS PER PAGE DOES NOT SEEM TO WORK SO REMOVED PAGING
# FOR NOW I HAVE CHOSEN TO NOT SHOW RESULTS THAT HAVE "NOT AVAILABLE" BUT INCLUDE THOSE THAT GIVE A DATE FOR WHEN IT WILL BE AVAILABLE
@route(PREFIX + '/showvideos', season=int, start=int)
def ShowVideos(title, url, season=0):

    oc = ObjectContainer(title2=title)
    try: data = HTML.ElementFromURL(url)
    except: return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    video_list = data.xpath('//div[contains(@class,"grid-item")]')
    for video in video_list:
        try: vid_avail = video.xpath('.//div[@class="message"]//text()')[0]
        except: vid_avail = 'Now'
        # Full episodes have a sub-header field for the title but all videos have a second header hidden text
        try: vid_title = video.xpath('.//div[@class="sub-header"]/span//text()')[0].strip()
        except: vid_title = video.xpath('.//div[@class="header"]/span[@class="hide"]//text()')[0].strip()
        thumb = video.xpath('.//div[@class=" imgDefered"]/@data-src')[0]
        seas_ep = video.xpath('.//div[@class="header"]/span//text()')[0].strip()
        if vid_avail == 'not available':
            continue
        if vid_avail == 'Now':
            vid_type = video.xpath('./@data-filter')[0]
            try: vid_url = video.xpath('./a/@href')[0]
            except: vid_url = None
            if not vid_url:
                continue
            # One descriptions is blank and gives an error
            try: desc = video.xpath('.//div[contains(@class,"deck")]/span//text()')[0].strip()
            except: desc = None
            other_info = video.xpath('.//div[@class="meta muted"]/small//text()')[0].strip()
            duration = Datetime.MillisecondsFromString(other_info.split(' - ')[0])
            date = Datetime.ParseDate(video.xpath('./@data-sort')[0])
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
            avail_title = 'NOT AVAILABLE UNTIL %s' %avail_date
            desc = '%s - %s' %(seas_ep, vid_title)
            oc.add(PopupDirectoryObject(key=Callback(NotAvailable, avail=vid_avail), title=avail_title, summary=desc, thumb=thumb))
      
    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos available to watch." )
    else:
        return oc
#################################################################################################################
# This function produces videos from the table layout used by old show video pages
# This function picks up all videos in all pages even without paging code
@route(PREFIX + '/showvideosold')
def ShowVideosOld(title, url, image=R(ICON), vid_type='Bonus'):
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
            except: thumb = image
        else:
            thumb = BASE_URL + thumb
        vid_url = BASE_URL + video.xpath('./@mainurl')[0]
        # need to add these videos to URL service
        if '/shows/' in vid_url:
            continue
        desc = video.xpath('./@maincontent')[0]
        date = video.xpath('./@mainposted')[0]
        if 'hrs ago' in date:
            date = Datetime.Now()
        else:
            date = Datetime.ParseDate(date)
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
@route(PREFIX + '/specialvideos', start=int)
def SpecialVideos(title, url):

    oc = ObjectContainer(title2=title)
    local_url = url.split('events/')[1].split('/')[0]
    feed_url = SPECIAL_AJAX + local_url + SPECIAL_AJAX2
    try:
        data = HTML.ElementFromURL(feed_url)
        video_list = data.xpath('//div[contains(@class, "item group video")]')
    except:
        # Some do not work with the feed so you have to just pull from the video page
        try:
            data = HTML.ElementFromURL(url + '/video.jhtml')
            video_list = data.xpath('//div[contains(@class, "grid-item grid-item")]')
            # Get the main player video
            thumb = data.xpath('//div[@id="mainPlayer"]//div[@class="imgDefered"]/@data-src')[0]
            oc.add(VideoClipObject(
                url = BASE_URL + data.xpath('//div[@id="mainPlayer"]/a/@href')[0], 
                title = data.xpath('//div[@id="mainPlayer"]//div[@class="header"]/span//text()')[0], 
                thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)
            ))
        except: return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    for video in video_list:
        try:
            vid_mgid = video.xpath('.//span/@data-content-uri')[0]
            vid_url = PLAYLIST_URL + vid_mgid.split('logotv.com:')[1].split('/')[0]
        except: vid_url = BASE_URL + video.xpath('.//a/@href')[0]
        thumb = video.xpath('.//div[@class="imgDefered"]/@data-src')[0]
        try: vid_title = video.xpath('.//div[@class="header"]/span/span//text()')[0].strip()
        except: vid_title = video.xpath('.//div[@class="header"]//span//text()')[0].strip()
        try: vid_desc = video.xpath('.//div[@class="deck"]/span[@class="fullText"]//text()')[0].strip()
        except: vid_desc = ''
        #date = video.xpath('.//span[@class="timestamp"]/@data-sort')[0]
        #date = Datetime.ParseDate(video.xpath('.//div[@class="meta muted"]/small//text()')[0])
        oc.add(VideoClipObject(
            url = vid_url, 
            title = vid_title, 
            thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON),
            #originally_available_at = date,
            summary = vid_desc
        ))
      
    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos available to watch." )
    else:
        return oc
