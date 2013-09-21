TITLE = 'Logo TV'
PREFIX = '/video/logotv'
ART = 'art-default.jpg'
ICON = 'icon-default.png'

BASE_URL = 'http://www.logotv.com'
SHOWS = 'http://www.logotv.com/shows/'
VIDEOS = 'http://www.logotv.com/video/showall.jhtml'
SEARCH_URL = 'http://www.logotv.com/search/video/'

RE_EPISODE  = Regex('.+Ep. (\d{1,3})')
RE_EPISODE_ALSO  = Regex('.+Episode (\d{1,3})')
#RE_EP_AND_SEASON  = Regex('.+Episode (\d{1,3}), Season (\d{1,2}).+')
####################################################################################################
# Set up containers for all possible objects
def Start():

  ObjectContainer.title1 = TITLE
  ObjectContainer.art = R(ART)

  DirectoryObject.thumb = R(ICON)
  DirectoryObject.art = R(ART)
  EpisodeObject.thumb = R(ICON)
  EpisodeObject.art = R(ART)
  VideoClipObject.thumb = R(ICON)
  VideoClipObject.art = R(ART)

  #HTTP.CacheTime = CACHE_1HOUR 
 
#####################################################################################
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu():
  oc = ObjectContainer()
  oc.add(DirectoryObject(key=Callback(LogoShows, title='Logo Shows'), title='Logo Shows')) 
  oc.add(DirectoryObject(key=Callback(LogoVideos, title='Logo Videos'), title='Logo Videos')) 
  #To get the InputDirectoryObject to produce a search input in Roku, prompt value must start with the word "search"
  oc.add(InputDirectoryObject(key=Callback(SearchVideos, title='Search Logo Videos'), title='Search Logo Videos', summary="Click here to search videos", prompt="Search for the videos you would like to find"))
  return oc
#####################################################################################
# For Logo main sections of Shows
@route(PREFIX + '/logoshows')
def LogoShows(title):
  oc = ObjectContainer(title2=title)
  oc.add(DirectoryObject(key=Callback(MoreVideos, title='Original Shows', show_type='original-series', url=SHOWS), title='Original Shows')) 
  oc.add(DirectoryObject(key=Callback(MoreVideos, title='Movies', show_type='movies-series', url=SHOWS), title='Movies')) 
  oc.add(DirectoryObject(key=Callback(MoreVideos, title='Other Shows', show_type='other-series', url=SHOWS), title='Other Shows')) 
  oc.add(DirectoryObject(key=Callback(MoreVideos, title='Comedy Shows and Special Shows', show_type='comedy-specials', url=SHOWS), title='Comedy Shows and Specials')) 
  oc.add(DirectoryObject(key=Callback(ProduceShows, title='All Logo Shows'), title='All Logo Shows')) 
  return oc
#####################################################################################
# For Logo main sections of Videos
@route(PREFIX + '/logovideos')
def LogoVideos(title):
  oc = ObjectContainer(title2=title)
  oc.add(DirectoryObject(key=Callback(MoreVideos, title='Full Episodes', show_type='full-episodes', url=VIDEOS), title='Full Episodes')) 
  oc.add(DirectoryObject(key=Callback(MoreVideos, title='Full Length Movies', show_type='full-movies', url=VIDEOS), title='Full Length Movies')) 
  oc.add(DirectoryObject(key=Callback(MoreVideos, title='Other Series and Specials', show_type='other-series', url=VIDEOS), title='Other Series and Specials')) 
  oc.add(DirectoryObject(key=Callback(MoreVideos, title='Previews and Bonus Clips', show_type='extras', url=VIDEOS), title='Previews and Bonus Clips')) 
  return oc
#####################################################################################
# For Producing All Shows 
@route(PREFIX + '/produceshows')
def ProduceShows(title):
  oc = ObjectContainer(title2=title)
  #THIS DATA PULL IS ALSO USED FOR SHOW SECTIONS
  data = HTML.ElementFromURL(SHOWS)
  #data = HTML.ElementFromURL(url, cacheTime = CACHE_1HOUR)
  for video in data.xpath('//div[@class="a_to_z_item"]/a'):
    url = video.xpath('.//@href')[0]
    if not url.startswith('http://'):
      url = BASE_URL + url
    title = video.xpath('.//text()')[0]
    if '/season_' in url:
      season = url.split('/season_')[1]
      season = season.split('/')[0]
    else:
      season = 1
    # USED THE OPTION OF ADDING THEM AS CALLBACKS TO DIRECTORYOBJECTS PER MIKE'S SUGGESTION
    # USED THE OPTION OF ADDING THEM AS CALLBACKS TO DIRECTORYOBJECTS PER MIKE'S SUGGESTION
    oc.add(DirectoryObject(key=Callback(ShowVideos, title=title, url=url, season=int(season)), title = title, thumb = Callback(GetThumb, url=url, fallback=R(ICON))))

  oc.objects.sort(key = lambda obj: obj.title)

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="There are shows to list right now.")
  else:
    return oc
#########################################################################################
# This will produce the carousels for logo main show and main video pages
# the choices for videos are full-episodes, full-movies, other-series and extras for logo
# the choices for shows are original-series, movies-series, other-series and comedy-speicials for logo
@route(PREFIX + '/morevideos')
def MoreVideos(title, url, show_type):
  oc = ObjectContainer(title2=title)
  #data = HTML.ElementFromURL(url)
  data = HTML.ElementFromURL(url, cacheTime=CACHE_1DAY)
  for video in data.xpath('//div[@id="carousel-%s"]/div[@class="itemContent"]' %show_type):
    vid_url = video.xpath('./a//@href')[0]
    if not vid_url.startswith('http://'):
      if not 'www.logotv.com' in vid_url:
        vid_url = BASE_URL + vid_url
      else:
        vid_url = 'http://' + vid_url
    else:
      if not vid_url.startswith('http://www.logotv.com'):
        continue
    title = video.xpath('./a/div[@class="title"]//text()')[0]
    thumb = video.xpath('./a/div[@class="image"]/img//@src')[0].split('?')[0]
    if not thumb.startswith('http://'):
      thumb = BASE_URL + thumb
    Log('the value of vid_url is %s' %vid_url)
    if 'series' in vid_url:
      if '/season_' in vid_url:
        season = vid_url.split('/season_')[1]
        season = season.split('/')[0]
      else:
        season = 1
      oc.add(DirectoryObject(key=Callback(ShowVideos, title=title, url=vid_url, season=int(season)), title = title, thumb = thumb))
    else:
      date = Datetime.ParseDate(video.xpath('./a/div[@class="addedDate"]//text()')[0])
      oc.add(VideoClipObject(
        url = vid_url, 
        title = title, 
        thumb = thumb,
        ))

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="There are no videos to list right now.")
  else:
    return oc
#################################################################################################################
# This function produces videos from the table layout used by show video pages for all three networks
# This function picks up all videos in all pages even without paging code
# IT PRODUCES VIDEOS EXACTLY HOW THE SITE DOES SO JERSEY SHORE SEASON 5 AND 6 SHOW ALL SEASONEPISODES
@route(PREFIX + '/showvideos', season=int)
def ShowVideos(title, url, season):
  oc = ObjectContainer(title2=title)
  local_url = url
  data = HTML.ElementFromURL(local_url)
  for video in data.xpath('//ol/li[@itemtype="http://schema.org/VideoObject"]'):
    # Logo has extra section of same videos that are picked up so put it in a try
    try:
      format_check = video.xpath('.//@mainuri')[0]
    except:
      continue
    other_info = video.xpath('.//@maintitle')[0]
    episode = video.xpath('./ul/li[@class="list-ep"]//text()')[0]
    if episode == '--' or episode == 'Special':
      episode = EpisodeFind(other_info)
    else:
      episode = int(episode)
    title = video.xpath('./meta[@itemprop="name"]//@content')[0]
    if not title:
      title = other_info
    thumb = video.xpath('./meta[@itemprop="thumbnail"]//@content')[0]
    if not thumb.startswith('http://'):
      thumb = BASE_URL + thumb
    thumb = thumb.split('?')[0]
    vid_url = video.xpath('./meta[@itemprop="url"]//@content')[0]
    if not vid_url.startswith('http://'):
      vid_url = BASE_URL + vid_url
    desc = video.xpath('./meta[@itemprop="description"]//@content')[0]
    date = video.xpath('./ul/li[@class="list-date"]//text()')[0]
    if 'hrs ago' in date:
      try:
        date = Datetime.Now()
      except:
        date = ''
    else:
      date = Datetime.ParseDate(date)

    oc.add(EpisodeObject(
      url = vid_url, 
      season = season,
      index = episode,
      title = title, 
      thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON),
      originally_available_at = date,
      summary = desc
    ))
  #oc.objects.sort(key = lambda obj: obj.originally_available_at, reverse=True)

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="There are no videos to list right now.")
  else:
    return oc
#########################################################################################
# This function is for pulling CMT Full Episodes from sections on the main and show page
# NEED TO DECIDE IF WE WANT TO USE THIS FOR CMT MOST POPULAR OR THE NEW VH1 PULL  ?q=%s
@route(PREFIX + '/searchvideos')
def SearchVideos(title, query='', page_url=''):
  oc = ObjectContainer(title2=title)
  if query:
    local_url = SEARCH_URL + '?q=' + String.Quote(query, usePlus = False)  + '&page=1'
  else:
    local_url = SEARCH_URL + page_url
  #data = HTML.ElementFromURL(local_url)
  data = HTML.ElementFromURL(local_url, cacheTime=CACHE_1HOUR)
  for item in data.xpath('//ul/li[contains(@class,"mtvn-video ")]'):
    link = item.xpath('./div/a//@href')[0]
    if 'mtviggy' in link:
      continue
    if not link.startswith('http://'):
      link = BASE_URL + link
    image = item.xpath('./div/a/span/img//@src')[0]
    if not image.startswith('http://'):
      image = BASE_URL + image
    try:
      video_title = item.xpath('./div/a/text()')[2].strip()
    except:
      video_title = item.xpath('./div/div/a/text()')[0]
    if not video_title:
      try:
        video_title = item.xpath('./div/a/span/span/text()')[0]
        video_title2 = item.xpath('./div/a/span/em/text()')[0]
        video_title = video_title + ' ' + video_title2
      except:
        video_title = ''
    try:
      date = item.xpath('./p/span/em//text()')[0]
      if date.startswith('Music'):
        date = item.xpath('./p/span/em//text()')[1]
    except:
      date = ''
    if 'hrs ago' in date:
      try:
        date = Datetime.Now()
      except:
        date = ''
    else:
      date = Datetime.ParseDate(date)

    oc.add(VideoClipObject(url=link, title=video_title, originally_available_at=date, thumb=Resource.ContentsOfURLWithFallback(url=image, fallback=ICON)))
  # This goes through all the pages of a search
  # After first page, the Prev and Next have the same page_url, so have to check for
  try:
    page_type = data.xpath('//a[contains(@class,"pagination")]//text()')
    x = len(page_type)-1
    if 'Next' in page_type[x]:
      page_url = data.xpath('//a[contains(@class,"pagination")]//@href')[x]
      oc.add(NextPageObject(
        key = Callback(SearchVideos, title = title, page_url = page_url), 
        title = L("Next Page ...")))
    else:
      pass
  except:
    pass

  #oc.objects.sort(key = lambda obj: obj.index, reverse=True)

  if len(oc)==0:
    return ObjectContainer(header="Sorry!", message="No video available in this category.")
  else:
    return oc
###########################################################################################
# This function is used in CreateShowSeasons and ShowVideo to pull episode numbers for shows that have '--' in episode field
@route(PREFIX + '/episodefind')
def EpisodeFind(other_info):
  try:
    # A couple of shows do not have an episode number but do have the episode number in other info in the format of Ep. or Episode 
    episode = int(RE_EPISODE.search(other_info).group(1))
  except:
    try:
      episode = int(RE_EPISODE_ALSO.search(other_info).group(1))
    except:
      episode = 0
  #Log('the value of episode at the end of the EpisodeFind function is %s' %episode)
  return episode
#############################################################################################################################
# This is a function to pull the thumb image from a page. 
# We first try the top of the page if it isn't there, we can pull an image from the video page side block
@route(PREFIX + '/gethumb')
def GetThumb(url, fallback):
  # NEED TO BE AWARE OF OTHER PULLS TO THIS URL AND MAKE SURE THEY ARE ALL THE SAME CACHE
  try:
    thumb = HTML.ElementFromURL(url, cacheTime = CACHE_1HOUR).xpath('//a[@class="marquee_img"]/img//@src')[0]
  except:
    try:
      thumb = HTML.ElementFromURL(url, cacheTime = CACHE_1HOUR).xpath("//head//meta[@property='og:image']//@content")[0]
    except:
      thumb = None
  if thumb:
    if '?' in thumb:
      thumb = thumb.split('?')[0]
    if not thumb.startswith('http://'):
      thumb = BASE_URL + thumb
    return Redirect(thumb)
  else:
    return Redirect(fallback)
