# -*- coding: utf-8 -*-
"""
Created on Sun Nov 28 15:44:39 2021

@author: manoila
"""

import requests
import musicbrainzngs
import pandas as pd
import time
import sys

print("Lyrics word counter v1 by Cristina Manoila")  
#Create user agent for musicbrainzngs API based on app name, version and contact - either email or url
userag = musicbrainzngs.set_useragent("My tech app", "1.0.0", contact="cristina_manoila28@yahoo.com") 

def retry_connection(retries,max_retries):
    """Retry the network connection in case of dropping based on
    the max_retries reached """
    wait = retries * 3
    print ('\rNetwork Error! Waiting %s secs and retrying...                      ' % wait,end='') 
    sys.stdout.flush()
    time.sleep(wait)
    retries += 1
    if retries > max_retries:
        print('\nCould not connect to network, Exiting ...')
        sys.exit('Exit Program')   
    return retries

def API_Search_artist(artist_input):
    """Search artist using musicbrainzngs API where:
    retries, max_retries, and success are variables for retrying 
    the network connection"""
    #variables defined for retrying the network connection
    retries,max_retries,success = 1, 3, False
    while not success and retries <= max_retries:
        try:
            #Search for artist in musicbrainzngs API if there's network connection
            response = musicbrainzngs.search_artists(artist = artist_input)['artist-list']
            success = True
            time.sleep(0.01)
            sys.stdout.flush()
            return response
        except Exception:
            #Retry to reconnect
            retries = retry_connection(retries,max_retries)

def API_Browse_recordings(id_art, limit_art, offset_art):
    """Browse recordings using musicbrainzngs API where:
    retries, max_retries, and success are variables for retrying 
    the network connection"""
    retries,max_retries,success = 1, 3, False
    while not success and retries <= max_retries:
        try:
            #Browse for recordings in musicbrainzngs API if there's network connection
            response =  musicbrainzngs.browse_recordings(artist = id_art,includes = [],limit=limit_art,offset=offset_art)["recording-list"] 
            success = True
            time.sleep(0.01)
            sys.stdout.flush()
            return response
        except Exception:
            #Retry to reconnect
            retries = retry_connection(retries,max_retries)

def API_Get_lyrics(url):
    """Get lyrics song where retries, max_retries, and success
    are variables for retrying the network connection"""
    retries,max_retries,success = 1, 3, False
    while not success and retries <= max_retries:
        try:
            #Get lyrics from lyrics API if there's network connection
            response = requests.get(url).text 
            success = True
            time.sleep(0.01)
            sys.stdout.flush()
            return response
        except Exception:
            #Retry to reconnect
            retries = retry_connection(retries,max_retries)

def Validate_artist():
    """Validation of the artist"""
    artist_valid = False
    print("\nType the artist name and press Enter: ")
    while not artist_valid:
        list_dict_artist_id = [] 
        #The input added from the user        
        artist_input = input("> ")
        #Search for artist in musicbrainzngs API
        search_artist = API_Search_artist(artist_input) 
        #Find the IDs for the artist and create a list
        if len(search_artist) > 0:
            [list_dict_artist_id.append(search_artist[i]["id"]) for i in range(0,len(search_artist)) if search_artist[i]["name"] == artist_input]          
            if len(list_dict_artist_id) == 0:
                proposed_artist_name = search_artist[0]["name"]
                print("\nDid you mean[Y/N]: {}?".format(proposed_artist_name))
                if  input() == "Y":
                    artist_input = proposed_artist_name
                    [list_dict_artist_id.append(search_artist[i]["id"]) for i in range(0,len(search_artist)) if search_artist[i]["name"] == artist_input]              
                else:
                    print("\nPlease, retype the name of the artist and press Enter.")
                    continue
            song_list = Song_list(list_dict_artist_id)
            if len(song_list) == 0:
                print("\nNo songs found. Try typing another artist name again and press Enter.")
                continue
            else:
                artist_valid = True
                print(" \rSongs found: %d                                  " % (len(song_list)))                
        else:
            print("\nNo artist found. Try typing the artist name again and press Enter.")
    return  artist_input, song_list  
            

def Song_list(list_dict_artist_id):
    """Get the songs list where 50 songs are read sequentially"""
    song_list = []
    limit_art = 50
    offset_art = 0
    browse_rec_count = 0
    print("\nSearching for songs on the net...")    
    for pos_id,id_art in enumerate(list_dict_artist_id[:]):
        #Get the recording list
        browse_rec = API_Browse_recordings(id_art, limit_art, offset_art)
        if len(browse_rec) != 0: 
            #Extract the song title
            title_rec = list(pd.DataFrame(browse_rec)['title'])
            #Remove the duplicates
            [song_list.append(song) for song in title_rec if song not in song_list]
            browse_rec_count+=len(browse_rec)  
            print(" \rSongs found: %d                                      " % (len(song_list)), end = '')
            #Find if there are other recordings
            while len(browse_rec)>=limit_art:
                offset_art+=limit_art
                browse_rec_next = API_Browse_recordings(id_art, limit_art, offset_art)
                browse_rec = browse_rec_next
                title_rec = list(pd.DataFrame(browse_rec)['title'])
                [song_list.append(song) for song in title_rec if song not in song_list]
                browse_rec_count += len(browse_rec)
                print(" \rSongs found: %d                                 " % (len(song_list)), end = '')    
    return song_list

def lyrics_processing(lyrics):
    """Preprocess the lyrics"""
    lyrics_a = lyrics.replace(r"\n", " ")
    lyrics_b = lyrics_a.replace(r"\r", " ")
    text_list = list(lyrics_b.rsplit())
    words_count = len(text_list)
    return words_count

def API_word_average(song_list,artist_input):
    """Count the words and songs and make the average of words in the artistst'songs
    where: total_words_count and songs_count are defined for calculation the average"""
    total_words_count = 0
    songs_count = 0
    for _,title in enumerate(song_list):
        url = "https://api.lyrics.ovh/v1/"+ artist_input + "/" + title
        url_new = url.replace(" ","%20")    
        #Get the lyrics
        lyr = API_Get_lyrics(url_new)
        if "error" not in lyr:
            words_count = lyrics_processing(lyr)
            total_words_count += words_count
            songs_count += 1
            print("\rLyrics found for: %d of %d songs. Total words: %d" % (songs_count,len(song_list),total_words_count), end = '')
    print("\nLyrics not found for %d songs." % (len(song_list)-songs_count))
    if songs_count != 0:
        average = total_words_count // songs_count
        print("The average number of words in the artist' songs with lyrics identified is: {} ".format(average))
    else:
        print("No lyrics for songs found in the lyrics API identified and no average calculated")
      

def Main():
    exit_request = False
    while not exit_request:
        artist_input, song_list  = Validate_artist()
        API_word_average(song_list,artist_input)
        print("\nPress 'Y' to calculate the average of another artist, 'N' to exit program.")
        user_input = input(">")
        if user_input == "N":
            exit_request = True
            
        
if __name__ == "__main__":      
    Main()















      