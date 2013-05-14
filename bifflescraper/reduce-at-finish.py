import codecs
import os

def reduce_at_finish():
                keywords = {}
                filename = '/root/biffle-prototype/bifflescraper/keyword_map_snapshot'

                # Open the workfile and parse domains into a data structure
                # TODO: Is utf-8 needed?
                infile = codecs.open(filename, 'r', encoding='utf-8')

                try:
                        for line in infile.readlines():
                                (keyword, value) = line.split('\t')

                                if (keywords.has_key(keyword)):
                                        keywords[keyword] = keywords[keyword] + int(value)
                                else:
                                        keywords[keyword] = int(value)
                except ValueError:
                        print("Parse error at %s" % line)
                        # log.msg("Parse error at %s" % line, level=log.ERROR)

                infile.close()

                # Delete the original file
                if (os.path.isfile(filename)):
                        os.unlink(filename)
                else:
                        raise Exception("ERROR: Can't find keyword file for deletion")

                # Write the data structure to a file
                outfile = codecs.open(filename, 'a+', encoding='utf-8')
                for key, value in keywords.items():
                                outfile.write(key + '\t' + str(value) + '\n')
                outfile.close()

reduce_at_finish()
