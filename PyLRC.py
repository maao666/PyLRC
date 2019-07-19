#!/usr/local/bin/python3
import logging


class Lrc:
    '''
    Documentation PENDING
    '''

    current_timestamp_in_ms = 0
    _raw_lrc = ""

    '''For parsing individual line,
    the returning format is defined as:
    [
        (type, content)
        (type, content)
        
        i.e.
        ("lyrics", post-ms, minutes, seconds, milliseconds, text, [text-seg-list], ...)
        ("sub-timing", ())
        ("lyrics", post-ms, minutes, seconds, milliseconds, text, [text-seg-list], ...)
        ...
    ]
    where type is defined as:
    "lyrics" for text
    "sub-timing" for timing of each word (latin) / character (east-asian)

    "title" for song title ('ti' tag)
    "artist" for artist ('ar' tag)
    "album" for artist ('al' tag)
    "author" for lyrics file author ('by' tag)
    "composer" for composer ('mu' tag)
    "arranger" for arranger ('ma' tag)
    "writer" for lyrics writer ('lr' tag)

    "offset" for global offset **requires special handling** ('offset' tag)
    "total" for the total time interval in ms **requires special handling** ('total' tag)
        afterwhich, the lyrics will be empty
        '0' by default, in which case this restriction won't be applied

    '''
    _parsed_lrc = []
    _plain_lyrics_plain_text = ""
    '''
    '''
    _parsing_required = True

    def __init__(self, raw_lrc: str):
        # raw_lrc contains the entire raw LRC text
        self._raw_lrc = raw_lrc

    def _launch_parser(self):
        self._parsing_required = False
        pass

    def get_attribution_by(self, attribution_tag: str):
        if self._parsing_required:
            self._launch_parser()
        for lrc_line in self._parsed_lrc:
            if(lrc_line[0] == attribution_tag):
                return lrc_line[1]
        return ""

    def get_artist(self) -> str:
        return self.get_attribution_by("artist")

    def get_title(self) -> str:
        return self.get_attribution_by("title")

    def get_album(self) -> str:
        return self.get_attribution_by("album")

    def get_writer(self) -> str:
        return self.get_attribution_by("writer")

    def get_composer(self) -> str:
        return self.get_attribution_by("composer")

    def require_immediate_parsing(self):
        '''Force lrc parsing'''
        self._parsing_required = True

    def _parse_timestamp_text(self, timestamp: str) -> int:
        '''Parse timestamp like 00:01.001 to a integer in millisecond'''
        # Find minute
        time_colon_index = timestamp.find(':')
        time_minute = timestamp[0: time_colon_index]
        try:
            time_minute = int(time_minute)
        except:
            return -1
        # Find second
        time_dot_index = timestamp.find('.')
        time_second = timestamp[time_colon_index + 1: time_dot_index]
        try:
            time_second = int(time_second)
        except:
            return -1
        # Find millisec
        time_millisec = timestamp[time_dot_index + 1:]
        # In case it's in the format of [00:01.00] not [00:01.000]
        if len(time_millisec.strip()) < 3:
            try:
                time_millisec = int(time_millisec) * \
                    10**(3 - len(time_millisec.strip()))
            except:
                return -1
        try:
            time_millisec = int(time_millisec)
        except:
            return -1
        logging.debug('Got timestamp {0}:{1}.{2}'.format(
            time_minute, time_second, time_millisec))
        # Calculate total millisec
        return time_minute * 60 * 1000 + time_second * 1000 + time_millisec * 1

    def set_current_timestamp(self, timestamp: str):
        self.current_timestamp_in_ms = self._parse_timestamp_text(timestamp)

    def lrc_interpreter(self, lrcrawtext):
        lrc_line_list = lrcrawtext.split('\n')
        lrc_converted_list = []
        for individual_line in lrc_line_list:
            # To handle multiple timestamps like [00:01.00][00:04.29]Something
            while True:
                left_bracket_index = individual_line.find('[')
                right_bracket_index = individual_line.find(']')
                if left_bracket_index == -1 or right_bracket_index == -1:
                    break
                else:
                    timestamp_in_millisec = self._parse_timestamp_text(
                        individual_line[left_bracket_index + 1:right_bracket_index])
                    # Append new timestamp to a list
                    rightmost_bracket_index = individual_line.rfind(']')
                    lrc_converted_list.append(
                        (timestamp_in_millisec, individual_line[rightmost_bracket_index + 1:]))
                    logging.debug('Got {}'.format(lrc_converted_list[-1]))
                    # Trim current time stamp
                    individual_line = individual_line[right_bracket_index + 1:]

        return lrc_converted_list


if __name__ == "__main__":
    with open('sample.lrc', 'r') as file:
        data = file.read()
    lrcinstance = Lrc(data)
    lrcinstance._launch_parser()
    print(lrcinstance._parsed_lrc)
