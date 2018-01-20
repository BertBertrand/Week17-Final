import string
body_read_chars = 100


class x12_parser:
    #absolute positions
    #elem_seps = [3, 6, 17, 20, 31, 34, 50, 53, 69, 76, 81, 83, 89, 99, 101, 103]
    #relative positions to remainder_isa
    elem_seps = [0, 3, 14, 17, 28, 31, 47, 50, 66, 73, 78, 80, 86, 96, 98, 100]
    def __init__(self, gen_parser):
        self.gen_parser = gen_parser
        self.doc_dict = {}
        self.doc_dict['elem_sep'] = ""
        self.doc_dict['seg_term'] = ""
        self.doc_dict['sub_component_sep'] = ""
        self.doc_dict['send_qual'] = ""
        self.doc_dict['send_alias'] = ""
        self.doc_dict['rcv_qual'] = ""
        self.doc_dict['rcv_alias'] = ""
        self.doc_dict['icd'] = ""
        self.doc_dict['ict'] = ""
        self.doc_dict['icn'] = ""
        self.interchange_count = 0
        self.handler_class = self.gen_parser.edi_handler_class
    def add_transitions(self, state_machine):
        state_machine.add_state(self.header_seg)
        state_machine.add_state(self.body_seg)
        state_machine.add_state(self.end_seg)
    def header_seg(self, cargo):
        #re-initialize these values
        self.doc_dict['elem_sep'] = ""
        self.doc_dict['seg_term'] = ""
        self.doc_dict['sub_component_sep'] = ""
        self.doc_dict['send_qual'] = ""
        self.doc_dict['send_alias'] = ""
        self.doc_dict['rcv_qual'] = ""
        self.doc_dict['rcv_alias'] = ""
        self.doc_dict['icd'] = ""
        self.doc_dict['ict'] = ""
        self.doc_dict['icn'] = ""
        #print "header_seg"
        f, tag = cargo
        #print "done header_seg"
        self.rewind = f.tell()
        remainder_isa = f.read(103)
        elem_sep = remainder_isa[0]
        for position in range(103):
            #print remainder_isa[position]
            if position in self.elem_seps:
                if not remainder_isa[position] == elem_sep:
                    f.seek(-103, 1)
                    #print "Found char (%s) other than %s at remainder_isa position %s" % (remainder_isa[position], elem_sep, position)
                    return self.gen_parser.searching_header, (f, "")
            else:
                if remainder_isa[position] == elem_sep:
                    f.seek(-103, 1)
                    #print "Found elem_sep char (%s) non-elem_sep position - remainder_isa position %s" % (elem_sep, position)
                    return self.gen_parser.searching_header, (f, "")
        self.doc_dict['elem_sep'] = elem_sep
        self.doc_dict['seg_term'] = remainder_isa[-1]
        self.doc_dict['sub_component_sep'] = remainder_isa[-2]
        self.doc_dict['send_qual'] = string.strip(remainder_isa[29:31])
        self.doc_dict['send_alias'] = string.strip(remainder_isa[32:47])
        self.doc_dict['rcv_qual'] = string.strip(remainder_isa[48:50])
        self.doc_dict['rcv_alias'] = string.strip(remainder_isa[51:66])
        self.doc_dict['icd'] = string.strip(remainder_isa[67:73])
        self.doc_dict['ict'] = string.strip(remainder_isa[74:78])
        self.doc_dict['icn'] = string.strip(remainder_isa[87:96])
        #print self.doc_dict
        header_segment = tag + remainder_isa
        #print "Header seg::", header_segment
        if self.gen_parser.handled_to < self.gen_parser.start_curr_poten_doc:
            non_edi_handler = self.gen_parser.non_edi_handler_class()
            temp_tell = f.tell()
            f.seek(self.gen_parser.handled_to)
            read_len = self.gen_parser.start_curr_poten_doc - self.gen_parser.handled_to
            data = f.read(read_len)
            non_edi_handler.non_edi_data(data, self.gen_parser.handled_to, temp_tell)
            f.seek(temp_tell)
        self.edi_handler = self.gen_parser.edi_handler_class(self.doc_dict)
        self.interchange_count = self.interchange_count + 1
        self.edi_handler.interchange_count = self.interchange_count
        self.edi_handler.start_interchange(self.gen_parser.start_curr_poten_doc)
        self.edi_handler.segment(header_segment)
        tmp_char_arr = []
        while 1:
            next_char = f.read(1)
            tmp_char_arr.append(next_char)
            if next_char == self.doc_dict['elem_sep']:
                break
        tag = "".join(tmp_char_arr)
        if tag[-4:-1] == "IEA":
            return self.end_seg, (f, tag)
        else:
            return self.body_seg, (f, tag)
    def body_seg(self, cargo):
        f, tag = cargo
        #print "Working on", tag
        tmp_char_arr = []
        anchor = f.tell()
        chars = 0
        while 1:
            chunk = f.read(body_read_chars)
            #next_char = f.read(1)
            try:
                ndx = chunk.index(self.doc_dict['seg_term']) + 1
                seek_pos = anchor + chars + ndx
                f.seek(seek_pos)
                tmp_char_arr.append(chunk[:ndx])
                break
            except ValueError:
                chars = chars + body_read_chars
                tmp_char_arr.append(chunk)
            if len(chunk) < body_read_chars:
                self.edi_handler.error("Hit EOF in body_seg before getting to a segment terminator")
                return self.gen_parser.eof, f
        remainder_seg = "".join(tmp_char_arr)
        #print "body seg ::", tag + remainder_seg
        self.edi_handler.segment(tag + remainder_seg)
        tmp_char_arr = []
        while 1:
            next_char = f.read(1)
            tmp_char_arr.append(next_char)
            if next_char == self.doc_dict['elem_sep']:
                break
            elif next_char == "":
                self.edi_handler.error("Hit EOF in body_seg before getting to an element separator")
                return self.gen_parser.eof, ""
        tag = "".join(tmp_char_arr)
        if tag[-4:-1] == "IEA":
            return self.end_seg, (f, tag)
        else:
            return self.body_seg, (f, tag)
    def end_seg(self, cargo):
        f, tag = cargo
        remainder_iea = f.read(16)
        #print "remainder_iea:", remainder_iea
        try:
            seg_term_ndx = remainder_iea.index(self.doc_dict['seg_term'])
        except ValueError:
            #print "No segment terminator in iea"
            self.edi_handler.error("No segment terminator in IEA in end_seg")
            f.seek(self.rewind)
            return self.gen_parser.searching_header, (f, "")
        iea_array = string.split(remainder_iea, self.doc_dict['elem_sep'])
        if not len(iea_array) > 1:
            #make sure there are at least two elements - we'll only be concerned with the first two
            #print "iea_array was %s elements rather than 2" % len(iea_array)
            self.edi_handler.error("IEA has %s elements rather than 2" % len(iea_array))
            f.seek(self.rewind)
            return self.gen_parser.searching_header, (f, "")
        if not 0 < len(iea_array[0]) < 10:
            #make sure the length of the first element is between 1 and 9 inclusive
            #print "iea_array[0] was %s bytes long " % len(iea_array[0])
            self.edi_handler.error("iea_array[0] was %s bytes long " % len(iea_array[0]))
            f.seek(self.rewind)
            return self.gen_parser.searching_header, (f, "")
        iea02_array = string.split(iea_array[1], self.doc_dict['seg_term'])
        if not len(iea02_array[0]) == 9:
            #make sure the length of the second element is 9 exactly
            #print "iea02_array[0] was %s bytes long " % len(iea02_array[0])
            self.edi_handerl.error("iea02_array[0] was %s bytes long " % len(iea02_array[0]))
            f.seek(self.rewind)
            return self.gen_parser.searching_header, (f, "")
        extra_chars = len(remainder_iea) - seg_term_ndx
        f.seek(f.tell() - extra_chars)
        end_iea = remainder_iea[:seg_term_ndx + 1]
        full_iea = tag + end_iea
        self.edi_handler.segment(full_iea)
        self.edi_handler.end_interchange(f.tell())
        self.gen_parser.handled_to = f.tell() + 1
        #print "end seg::", full_iea
        return self.gen_parser.searching_header, (f, "")
