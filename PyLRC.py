#!/usr/local/bin/python3
import logging
import pprint
import json

__all__ = [
    "Lrc",
]


class Lrc:
    '''
    Documentation PENDING
    '''

    current_timestamp_in_ms = 0
    _raw_lrc = ""

    '''
    Dict format:
    {"title": "Foo",
    "artist": "Bar",
    "00010211": {"mimutes": 01,
                "seconds": 02,
                "milliseconds": 121,
                "translation": "Bonjour",
                "precise-timing": "<01><031><102>",
                "tr-precise-timing": "<01><031><102>",
                "text": "Hello",
                "tokenized": ["word1", "word2"][Optional]
                }
    "00013000": {"mimutes": 01,
                "seconds": 40,
                "milliseconds": 100,
                "translation": "Bonjour",
                "precise-timing": "<01><031><102>",
                "tr-precise-timing": "<01><031><102>",
                "text": "Hello",
                "tokenized": ["word1", "word2"][Optional]
                }
    }

    where key is defined as:
    "lyrics" for text
    "translation" for translation
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
    _parsed_lrc = {}
    _lyrics_plain_text = ""
    _global_offset = 0
    _global_total_time_in_ms = 0
    _parsing_required = False
    _tag_correspondance_dict = {"ti": "title",
                                "ar": "artist",
                                "al": "album",
                                "by": "author",
                                "mu": "composer",
                                "ma": "arranger",
                                "lr": "writer",
                                "offset": "offset",
                                "total": "total"}

    def __init__(self):
        # raw_lrc contains the entire raw LRC text
        pass

    def load(self, raw_lrc: str):
        '''Load LRC lyrics and parse it
        '''
        # raw_lrc contains the entire raw LRC text
        self._raw_lrc = raw_lrc
        self._launch_parser()
        self._get_plain_text()

    def load_from_file(self, filename: str):
        '''Load lyrics from a .LRC file
        Usage: 
        >>> your_lrc_instance.load_from_file('foobar.lrc')
        '''
        with open(filename, 'r') as lrc_file:
            self.load(lrc_file.read())

    def load_json(self, raw_json: str):
        '''Load lyrics from a json-format string
        '''
        self._parsed_lrc = json.loads(raw_json)
        self._get_plain_text()

    def load_json_from_file(self, filename: str):
        '''Load lyrics from a json-format file
        Usage: 
        >>> your_lrc_instance.load_json_from_file('foobar.json')
        '''
        with open(filename, 'r') as json_file:
            self.load_json(json_file.read())

    def export_json(self) -> str:
        '''Return the json format of the current lyrics so that it can be imported in the future
        Usage: 
        >>> your_lrc_instance.export_json()
        '''
        return json.dumps(self._parsed_lrc, sort_keys=False, indent=4)

    def export_json_to_file(self, filename: str):
        '''Export lyrics to a json-format file
        Usage: 
        >>> your_lrc_instance.export_json_to_file('foobar.json')
        '''
        with open(filename, 'w') as json_file:
            json_file.write(self.export_json())

    def export_lrc_to_file(self, filename: str):
        '''Export lyrics to a standard .LRC file
        Usage: 
        >>> your_lrc_instance.export_lrc_to_file('foobar.lrc')
        '''
        with open(filename, 'w') as lrc_file:
            lrc_file.write(self.export_lrc())

    def export_lrc(self) -> str:
        '''Return the LRC format of the current lyrics
        Usage: 
        >>> your_lrc_instance.export_lrc()
        '''
        lrc_text = ''
        if self._parsing_required:
            self._launch_parser()
        for tag_text, dict_iter in sorted(self._parsed_lrc.items(), key=lambda x: x[0]):
            if isinstance(tag_text, str) and not tag_text.isdigit():
                # In such case it's a tag
                lrc_text = "{0}[{1}:{2}]\n".format(
                    lrc_text,
                    list(self._tag_correspondance_dict.keys())[
                        list(self._tag_correspondance_dict.values()).index(tag_text)],
                    dict_iter)

        for tag_text, dict_iter in sorted(self._parsed_lrc.items(), key=lambda x: x[0]):
            if isinstance(tag_text, str) and tag_text.isdigit():
                # In such case it's a timestamp
                lrc_text = "{0}[{1:02d}:{2:02d}.{3:03d}]{4}\n".format(
                    lrc_text,
                    dict_iter.get("minutes"),
                    dict_iter.get("seconds"),
                    dict_iter.get("milliseconds"),
                    dict_iter.get("text"))
                if dict_iter.get("precise-timing", '').strip() != "":
                    lrc_text = "{0}[{1:02d}:{2:02d}.{3:03d}][tt]{4}\n".format(
                        lrc_text,
                        dict_iter.get("minutes"),
                        dict_iter.get("seconds"),
                        dict_iter.get("milliseconds"),
                        dict_iter.get("precise-timing"))
                if dict_iter.get("translation", '').strip() != "":
                    lrc_text = "{0}[{1:02d}:{2:02d}.{3:03d}][tr]{4}\n".format(
                        lrc_text,
                        dict_iter.get("minutes"),
                        dict_iter.get("seconds"),
                        dict_iter.get("milliseconds"),
                        dict_iter.get("translation"))

        return lrc_text

    def export_plain_lyrics(self) -> str:
        '''Return the plain text of the current lyrics
        Usage: 
        >>> your_lrc_instance.export_plain_lyrics()
        '''
        self._get_plain_text()
        return self._lyrics_plain_text

    def _tag_handler(self, tag_text: str):
        '''Parse a tag such as "[ar: someone]" to a key-value pair like {"artist": "someone"}
        and write it to the dict _parsed_lrc
        '''
        if tag_text.find(':') != -1:
            tag_list = [tag_text.strip()[tag_text.strip().find('[') + 1: tag_text.strip().find(':')], tag_text.strip()[
                tag_text.strip().find(':') + 1:tag_text.strip().find(']')]]
            tag_key = self._tag_correspondance_dict.get(
                tag_list[0].strip(), '')
            if tag_key != '':
                self._parsed_lrc[tag_key] = tag_list[1].strip()
            else:
                logging.info("Unexpected tag detected: {}".format(tag_list[0]))
        else:
            logging.info("Unable to extract tag for {}".format(tag_text))

    def _is_timestamp(self, tag_text: str):
        colon_index = tag_text.find(':')
        period_index = tag_text.find('.')
        if colon_index != -1\
                and period_index != -1\
                and tag_text[: colon_index].isdigit()\
                and tag_text[colon_index+1: period_index].isdigit()\
                and tag_text[period_index+1:].isdigit():
            # It's a timestamp!
            return True
        return False

    def _get_plain_text(self):
        if self._parsing_required:
            self._launch_parser()
        for ms, dict_iter in sorted(self._parsed_lrc.items(), key=lambda x: x[0]):
            if isinstance(ms, str) and ms.isdigit():
                self._lyrics_plain_text = "{}{}\n".format(
                    self._lyrics_plain_text, dict_iter.get("text"))
        self._lyrics_plain_text = self._lyrics_plain_text.strip()

    def _lyrics_handler(self, unparsed_lyrics_text: str):
        '''Parse string like "[01:23.456][02:00:001]Foobar"
        to the dict _parsed_lrc
        Also handles lyrics with precise timestamp that ismarked by [tt]
        and translations that are marked by [tr]
        '''
        timestamp_list = []
        is_translation = False
        is_precise_timing = False
        tag_begining_index = unparsed_lyrics_text.find('[')
        tag_ending_index = unparsed_lyrics_text.find(']')
        # Handle all the tags
        while tag_begining_index != -1 and tag_ending_index != -1:
            if self._is_timestamp(unparsed_lyrics_text[tag_begining_index+1: tag_ending_index]):
                # It's a timestamp
                timestamp_list.append(self._parse_timestamp_text(
                    unparsed_lyrics_text[tag_begining_index+1: tag_ending_index]))
            else:
                if unparsed_lyrics_text[tag_begining_index+1: tag_ending_index] == 'tr':
                    # It's a translation
                    is_translation = True

                if unparsed_lyrics_text[tag_begining_index+1: tag_ending_index] == 'tt':
                    # It's a precise timing definition
                    is_precise_timing = True
            # Trim labels
            unparsed_lyrics_text = unparsed_lyrics_text[tag_ending_index+1:]

            # Be prepared for the next round
            tag_begining_index = unparsed_lyrics_text.find('[')
            tag_ending_index = unparsed_lyrics_text.find(']')

        # Handle text
        for timestamp_iter in timestamp_list:
            updated_dict: dict = self._parsed_lrc.get('{0:08d}'.format(timestamp_iter[0]), {
                "minutes": timestamp_iter[1],
                "seconds": timestamp_iter[2],
                "milliseconds": timestamp_iter[3]}
            )
            if is_translation and not is_precise_timing:
                updated_dict["translation"] = unparsed_lyrics_text
            elif not is_translation and is_precise_timing:
                updated_dict["precise-timing"] = unparsed_lyrics_text
            elif is_translation and is_precise_timing:
                updated_dict["tr-precise-timing"] = unparsed_lyrics_text
            else:
                updated_dict["text"] = unparsed_lyrics_text
            # Write back
            self._parsed_lrc['{0:08d}'.format(
                timestamp_iter[0])] = updated_dict

    def _launch_parser(self):
        '''The root method for parser'''
        lrc_line_list = self._raw_lrc.split('\n')

        for individual_line in lrc_line_list:
            try:
                tag_text = individual_line[individual_line.find(
                    '[') + 1:individual_line.find(']')]
            except:
                logging.info(
                    "No label detected at \"{}\". Skipping...".format(individual_line))
            if self._is_timestamp(tag_text):
                self._lyrics_handler(individual_line)
            else:
                self._tag_handler(individual_line)

        self._parsing_required = False

    def get_attribution_by(self, attribution_tag: str):
        if self._parsing_required:
            self._launch_parser()
        self._parsed_lrc.get(attribution_tag, '')

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

    def _parse_timestamp_text(self, timestamp: str) -> list:
        '''Parse timestamp like "00:01.001" to a list
        Returning format:
        [total ms, minutes, seconds, milliseconds]
        Warning: only total_ms is affected by _global_offset'''
        # Get minute
        time_colon_index = timestamp.find(':')
        time_minute = timestamp[0: time_colon_index]
        time_minute = int(time_minute)

        # Get second
        time_dot_index = timestamp.find('.')
        time_second = timestamp[time_colon_index + 1: time_dot_index]
        time_second = int(time_second)

        # Get millisec
        time_millisec = timestamp[time_dot_index + 1:]
        # In case it's in the format of [00:01.00] not [00:01.000]
        if len(time_millisec.strip()) < 3:
            time_millisec = int(time_millisec) * \
                10**(3 - len(time_millisec.strip()))
        time_millisec = int(time_millisec)
        logging.debug('Got timestamp {0}:{1}.{2}'.format(
            time_minute, time_second, time_millisec))
        # Calculate total millisec
        total_ms = time_minute * 60 * 1000 + time_second * 1000 + time_millisec * 1
        return [total_ms + self._global_offset, time_minute, time_second, time_millisec]

    def set_current_timestamp(self, timestamp: str):
        self.current_timestamp_in_ms = self._parse_timestamp_text(timestamp)[0]

    def lrc_interpreter(self, lrcrawtext):
        '''Obsolete method'''
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


def _perfcheck():
    with open('sample.lrc', 'r') as lrcfile:
        data = lrcfile.read()
        lrcinstance = Lrc()
        lrcinstance.load(data)
    lrcinstance.export_json_to_file("sample.json")

    lrcinstance2 = Lrc()
    lrcinstance2.load_json_from_file("sample.json")
    pprint.pprint(lrcinstance2._parsed_lrc)
    print(lrcinstance2.export_lrc())


if __name__ == "__main__":
    _perfcheck()
