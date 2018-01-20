import string
from xml.dom import minidom
dom_impl = minidom.DOMImplementation()

#MAPPING DICTIONARIES
functional_identifier_map = {'PO': 'Purchase Order'}
transaction_set_identifier_map = {'850': 'Purchase Order'}
purpose_code_map = {'22': 'Information Copy'}
type_code_map = {'NE': 'New Order'}
shipment_method_code_map = {'DF': 'Defined by Buyer and Seller'}
location_qual_map = {'ZZ': "Mutually Defined"}
date_time_map = {'002': "Ship No Later", '037': "Ship not before", '038': "Ship not after"}
carrier_quantity_map = {"CNT90": "Standard Container"}
carrier_equip_dtls = {'40': "40 ft. Open Top Container"}
entity_identifier_code_map = {"SE": "Selling Party", "OB": "Ordered By", "CT": ""}
identification_code_map = {"92": "Assigned by Buyer or Buyer's Agent", "38": "", "": ""}
reference_number_qual_map = {"DP": "Department Number", "": ""}
reference_number_map = {"101": "Swimwear", "": ""}
unit_code_map = {"EA": "Each", "": ""}
service_id_code_map = {"ZZ": "Mutually Defined", "HD": "Hierarchy Defined", "": ""}
product_description_code_map = {"F": "Free Form", "": ""}

class GenericEDIHandler:
    def __init__(self, doc_dict):
        self.doc_dict = doc_dict
    def start_interchange(self, begin_fp):
        print "*" * 40
        print "Starting interchange"
        print "doc_dict>>", str(self.doc_dict)
    def end_interchange(self, end_fp):
        print "Ending interchange"
        print "*" * 40
    def segment(self, segment):
        print "segment-->>", segment
    def error(self, message):
        print "ERROR>>"
        print message
        print "ERROR>>"

class Translator:
    def __init__(self, doc_dict):
        self.doc_dict = doc_dict
        #import edi_loop
        from xml.dom import minidom
        self.schema = minidom.parse('/mnt/batch/tasks/shared/x12_schema.xml')
        self.curr_seg = self.schema # initialize curr_seg to EDI description DOM - as parsing occurs/continues, it will point to the DOM node of the current EDI segment
        self.is_error = False
        self.loop_dict = {} # keeps track of how many times each segment was encountered
        #self.xml_repr_dict = {}
        self.xml_out_dict = {} # this points to the *last* occurence of an output DOM node for each EDI segment - the key is the <tag>_<id> derived from the XML description of the EDI document
    def non_text_child_nodes(self, nd):
        '''Return list of non-text nodes which are children of nd'''
        return filter(lambda x: x.nodeType != self.schema.TEXT_NODE, nd.childNodes)
    def validate_seg(self, segment):
        '''Return pointer to DOM object of EDI segment schema if segment is valid - otherwise return None'''
        #check current segment for repeats
        try:
            if (str(self.curr_seg.getAttribute('tag')) == segment) and (int(self.curr_seg.getAttribute('max_use')) > 1):
                return self.curr_seg
        except AttributeError:
            #probably on a root element
            pass
        #search child nodes first
        for child_node in self.non_text_child_nodes(self.curr_seg):
            if (str(child_node.getAttribute('tag')) == segment):
                return child_node
            if (str(child_node.getAttribute('req')) == "M") and (not self.loop_dict.has_key(child_node.getAttribute('tag') + "_" + child_node.getAttribute('id'))):
                self.error('Mandatory tag < %s > was passed over while searching child nodes' % child_node.getAttribute('tag'))
                return None
        was_curr_seg = self.curr_seg
        tmp_curr_seg = was_curr_seg.nextSibling
        counter = 0
        while 1:
            counter += 1
            #check self for None
            if tmp_curr_seg == None:
                #if there is a parent node, set was_curr_seg to it
                if was_curr_seg.parentNode:
                    was_curr_seg = was_curr_seg.parentNode
                    tmp_curr_seg = was_curr_seg
                    continue
                self.error('Reached end of doc without matching < %s >' % segment)
                return None
            #check self for text node
            if tmp_curr_seg.nodeType == tmp_curr_seg.TEXT_NODE:
                was_curr_seg = tmp_curr_seg
                tmp_curr_seg = tmp_curr_seg.nextSibling
                continue
            #check self for match
            if tmp_curr_seg.getAttribute('tag') == segment:
                return tmp_curr_seg
            #check self for mandatory
            elif (str(tmp_curr_seg.getAttribute('req')) == "M") and (not self.loop_dict.has_key(str(tmp_curr_seg.getAttribute('tag') + "_" + tmp_curr_seg.getAttribute('id')))):
                self.error('Mandatory tag < %s > with loop id < %s > was passed over' % (tmp_curr_seg.getAttribute('tag'), str(tmp_curr_seg.getAttribute('tag') + tmp_curr_seg.getAttribute('id'))))
                return None
            else:
                was_curr_seg = tmp_curr_seg
                tmp_curr_seg = tmp_curr_seg.nextSibling
    def start_interchange(self, begin_fp):
        self.interchange_xml = dom_impl.createDocument('', 'Interchange', '')
    def end_interchange(self, end_fp):
        outfile = open('%s_%s.xml' % (self.xml_prefix, self.interchange_count), 'w')
        outfile.write(self.interchange_xml.toprettyxml())
        outfile.close()
    def segment(self, segment):
        if not self.is_error:
            mod_segment = string.replace(segment, self.doc_dict['seg_term'], '')
            elements = string.split(mod_segment, self.doc_dict['elem_sep'])
            segment_tag = elements[0]
            self.curr_seg = self.validate_seg(segment_tag)
            if not self.curr_seg:
                self.error('Invalid segment :: %s' % segment)
                return
            this_id = str(self.curr_seg.getAttribute('tag') + "_" + self.curr_seg.getAttribute('id'))
            self.loop_dict[this_id] = self.loop_dict.get(this_id, 0) + 1
            #this_id = self.curr_seg.getAttribute('tag') + self.curr_seg.getAttribute('id')
            tmp_seg = string.replace(segment, self.doc_dict['seg_term'], '')
            elements = string.split(tmp_seg, self.doc_dict['elem_sep'])
            getattr(self, "do_%s" % segment_tag)(elements, this_id)
    def error(self, message):
        self.is_error = True
        print "ERROR>>"
        print message
        print "ERROR>>"

    def do_ISA(self, elements, this_id):
        '''<Interchange>
        <AuthorizationInformation id="" qualifier=""/>
        <SecurityInformation id="" qualifier=""/>
        <Sender id="SENDER" qualifier="ZZ"/>
        <Receiver id="RECEIVER" qualifier="ZZ"/>
        <DateTime date="041201" time="1200"/>
        <EdiControlInformation standards_id="U" version_number="00305" number="000000101"/>
        <AcknowledgementRequested id="1"/>
        <TestIndicator id="P"/>'''
        self.loop_dict = {}
        self.loop_dict['ISA_1'] = 1
        self.xml_out_dict['ISA_1'] = self.interchange_xml.documentElement
        #authorization_info
        authorization_info = self.interchange_xml.createElement('AuthorizationInformation')
        authorization_info.setAttribute('id', string.strip(elements[2]))
        authorization_info.setAttribute('qualifier', string.strip(elements[1]))
        self.xml_out_dict['ISA_1'].appendChild(authorization_info)
        #security_info
        security_info = self.interchange_xml.createElement('SecurityInformation')
        security_info.setAttribute('id', string.strip(elements[4]))
        security_info.setAttribute('qualifier', string.strip(elements[3]))
        self.xml_out_dict['ISA_1'].appendChild(security_info)
        #sender_info
        sender_info = self.interchange_xml.createElement('Sender')
        sender_info.setAttribute('id', string.strip(elements[6]))
        sender_info.setAttribute('qualifier', string.strip(elements[5]))
        self.xml_out_dict['ISA_1'].appendChild(sender_info)
        #receiver_info
        receiver_info = self.interchange_xml.createElement('Receiver')
        receiver_info.setAttribute('id', string.strip(elements[8]))
        receiver_info.setAttribute('qualifier', string.strip(elements[7]))
        self.xml_out_dict['ISA_1'].appendChild(receiver_info)
        #datetime
        date_time = self.interchange_xml.createElement('DateTime')
        date_time.setAttribute('date', string.strip(elements[9]))
        date_time.setAttribute('time', string.strip(elements[10]))
        self.xml_out_dict['ISA_1'].appendChild(date_time)
        #edi_control_info
        date_time = self.interchange_xml.createElement('EdiControlInformation')
        date_time.setAttribute('standards_id', string.strip(elements[11]))
        date_time.setAttribute('version_number', string.strip(elements[12]))
        date_time.setAttribute('number', string.strip(elements[13]))
        self.xml_out_dict['ISA_1'].appendChild(date_time)
        #ack_request
        ack_req = self.interchange_xml.createElement('AcknwledgementRequested')
        ack_req.setAttribute('id', string.strip(elements[14]))
        self.xml_out_dict['ISA_1'].appendChild(ack_req)
        #test_production
        test_production = self.interchange_xml.createElement('TestIndicator')
        test_production.setAttribute('id', string.strip(elements[15]))
        self.xml_out_dict['ISA_1'].appendChild(test_production)
    def do_GS(self, elements, this_id):
        '''<FunctionalGroup number_of_transaction_sets="1">
        <FunctionalIdentifier code="PO" name="Purchase Order"/>
        <Sender id="SENDER"/>
        <Receiver id="Receiver"/>
        <DateTime date="041201" time="1200"/>
        <Control number="101"/>
        <EdiIndustryIdentifier code="X" id="003050"/>'''
        seg_list = ['ISA_1']
        for key in self.loop_dict.keys():
            if key not in seg_list:
                del(self.loop_dict[key])
        self.loop_dict['GS_2'] = 1
        self.xml_out_dict['GS_2'] = self.interchange_xml.createElement('FunctionalGroup')
        self.xml_out_dict['ISA_1'].appendChild(self.xml_out_dict['GS_2'])
        #functional_identifier
        functional_identifier = self.interchange_xml.createElement('FunctionalIdentifier')
        functional_identifier.setAttribute('code', elements[1])
        functional_identifier.setAttribute('name', functional_identifier_map.get(elements[1], 'Unknown Functional Code Type'))
        self.xml_out_dict['GS_2'].appendChild(functional_identifier)
        #sender
        sender = self.interchange_xml.createElement('Sender')
        sender.setAttribute('id', elements[2])
        self.xml_out_dict['GS_2'].appendChild(sender)
        #receiver
        receiver = self.interchange_xml.createElement('Receiver')
        receiver.setAttribute('id', elements[3])
        self.xml_out_dict['GS_2'].appendChild(receiver)
        #date_time
        date_time = self.interchange_xml.createElement('DateTime')
        date_time.setAttribute('date', elements[4])
        date_time.setAttribute('time', elements[5])
        self.xml_out_dict['GS_2'].appendChild(date_time)
        #control
        control = self.interchange_xml.createElement('Control')
        control.setAttribute('number', elements[6])
        self.xml_out_dict['GS_2'].appendChild(control)
        #edi_industry_id
        edi_industry_id = self.interchange_xml.createElement('EdiIndustryIdentifier')
        edi_industry_id.setAttribute('code', elements[7])
        edi_industry_id.setAttribute('id', elements[8])
        self.xml_out_dict['GS_2'].appendChild(edi_industry_id)
    def do_ST(self, elements, this_id):
        '''<TransactionSet>
        <Id code="850" name="Purchase Order"/>
        <ControlNumber value="000000101"/>'''
        seg_list = ['ISA_1', 'GS_2']
        for key in self.loop_dict.keys():
            if key not in seg_list:
                del(self.loop_dict[key])
        self.loop_dict['ST_3'] = 1
        self.xml_out_dict['ST_3'] = self.interchange_xml.createElement('TransactionSet')
        self.xml_out_dict['GS_2'].appendChild(self.xml_out_dict['ST_3'])
        #id
        id = self.interchange_xml.createElement('Id')
        id.setAttribute('code', elements[1])
        id.setAttribute('name', transaction_set_identifier_map.get(elements[1], 'Unknown Transaction Set Identifier'))
        self.xml_out_dict['ST_3'].appendChild(id)
        #control_number
        control_number = self.interchange_xml.createElement('ControlNumber')
        control_number.setAttribute('value', elements[2])
        self.xml_out_dict['ST_3'].appendChild(control_number)
    def do_BEG(self, elements, this_id):
        '''<PoInfo>
        <Purpose code="22" name="Information Copy"/>
        <Type code="NE" name="New Order"/>
        <Number value="101"/>
        <DateTime date="041201"/>
        <ContractNumber value="123456"/>
        </PoInfo>'''
        #po_info
        po_info = self.interchange_xml.createElement('PoInfo')
        self.xml_out_dict['ST_3'].appendChild(po_info)
        #purpose
        purpose = self.interchange_xml.createElement('Purpose')
        purpose.setAttribute('code', elements[1])
        purpose.setAttribute('name', purpose_code_map.get(elements[1], "Unknown Purpose Code"))
        po_info.appendChild(purpose)
        #type
        type = self.interchange_xml.createElement('Type')
        type.setAttribute('code', elements[2])
        type.setAttribute('name', type_code_map.get(elements[2], "Unknown Purpose Code"))
        po_info.appendChild(type)
        #number
        number = self.interchange_xml.createElement('Number')
        number.setAttribute('value', elements[3])
        po_info.appendChild(number)
        #datetime
        datetime = self.interchange_xml.createElement('DateTime')
        datetime.setAttribute('date', elements[5])
        po_info.appendChild(datetime)
        #contract_number
        contract_number = self.interchange_xml.createElement('ContractNumber')
        contract_number.setAttribute('value', elements[6])
        po_info.appendChild(contract_number)

    def do_FOB(self, elements, this_id):
        '''<FOBInstructions>
        <ShipmentMethodOfPayment code="DF" description="Defined by Buyer and Seller"/>
        <Location qualifier="ZZ" description="Mutually Defined"/>
        <Description value="JMJ"/>
        </FOBInstructions>'''
        #fob_instructions
        fob_instructions = self.interchange_xml.createElement('FOBInstructions')
        self.xml_out_dict['ST_3'].appendChild(fob_instructions)
        #shipment_method_of_payment
        shipment_method_of_payment = self.interchange_xml.createElement('ShipmentMethodOfPayment')
        shipment_method_of_payment.setAttribute('code', elements[1])
        shipment_method_of_payment.setAttribute('description', shipment_method_code_map.get(elements[1], "Unknown Shipment Method of Payment Code"))
        fob_instructions.appendChild(shipment_method_of_payment)
        #location
        location = self.interchange_xml.createElement('Location')
        location.setAttribute('qualifier', elements[2])
        location.setAttribute('description', location_qual_map.get(elements[2], "Unknown Location Qualifier"))
        fob_instructions.appendChild(location)
        #description
        description = self.interchange_xml.createElement('Description')
        description.setAttribute('value', elements[3])
        fob_instructions.appendChild(description)
    def do_DTM(self, elements, this_id):
        '''<DateTimeReference qualifier="037" description="Ship Not Before" date="041205"/>
        <DateTimeReference qualifier="038" description="Ship Not After" date="041215"/>
        <DateTimeReference qualifier="002" description="Ship No Later" date="041218"/>'''
        #date_time_reference
        date_time_reference = self.interchange_xml.createElement('DateTimeReference')
        date_time_reference.setAttribute('qualifier', elements[1])
        date_time_reference.setAttribute('description', date_time_map.get(elements[1], "Unknown DTM qualifier"))
        date_time_reference.setAttribute('date', elements[2])
        self.xml_out_dict['ST_3'].appendChild(date_time_reference)
    def do_TD1(self, elements, this_id):
        '''<CarrierQuantityDetails>
            <Packaging code="CNT90" description="Standard Container"/>
            <Lading quantity="1"/>
        </CarrierQuantityDetails>'''
        #carrier_quantity_details
        carrier_quantity_details = self.interchange_xml.createElement('CarrierQuantityDetails')
        self.xml_out_dict['ST_3'].appendChild(carrier_quantity_details)
        #packaging
        packaging = self.interchange_xml.createElement('Packaging')
        packaging.setAttribute('code', elements[1])
        packaging.setAttribute('description', carrier_quantity_map[elements[1]])
        carrier_quantity_details.appendChild(packaging)
        #lading
        lading = self.interchange_xml.createElement('Lading')
        lading.setAttribute('quantity', elements[2])
        carrier_quantity_details.appendChild(lading)
    def do_TD5(self, elements, this_id):
        '''<CarrierRoutingDetails>
            <TransportationMethod code="JJ"/>
            <RoutingDescription value="X"/>
        </CarrierRoutingDetails>'''
        #carrier_routing_details
        carrier_routing_details = self.interchange_xml.createElement('CarrierRoutingDetails')
        self.xml_out_dict['ST_3'].appendChild(carrier_routing_details)
        #transport_method
        transport_method = self.interchange_xml.createElement('TransportationMethod')
        transport_method.setAttribute('code', elements[4])
        carrier_routing_details.appendChild(transport_method)
        #routing_desc
        routing_desc = self.interchange_xml.createElement('RoutingDescription')
        routing_desc.setAttribute('value', elements[5])
        carrier_routing_details.appendChild(routing_desc)
    def do_TD3(self, elements, this_id):
        '''<CarrierEquipmentDetails id="40" description="40 ft. Open Top Container"/>'''
        #carrier_equip_details
        carrier_equip_details = self.interchange_xml.createElement('CarrierEquipmentDetails')
        carrier_equip_details.setAttribute('id', elements[1])
        carrier_equip_details.setAttribute('description', carrier_equip_dtls[elements[1]])
        self.xml_out_dict['ST_3'].appendChild(carrier_equip_details)
    def do_N1(self, elements, this_id):
        '''<PartyIdentification>
            <Name>
                <EntityIdentifier code="SE" description="Selling Party"/>
                <PartyName value="Foo Bar Sellers"/>
                <IdentificationCode qualifier="92" qual_description="Assigned by Buyer or Buyer's Agent" description="7759"/>
            </Name>
            <GeographicLocation country="US"/>
            <ReferenceNumbers qualifier="DP" qual_description="Department Number" number="101" number_description="Swimwear"/>
        </PartyIdentification>'''
        #party_identification
        party_identification = self.interchange_xml.createElement('PartyIdentification')
        self.xml_out_dict[this_id] = party_identification
        #name
        name = self.interchange_xml.createElement('Name')
        party_identification.appendChild(name)
        #entity_identifier
        entity_identifier = self.interchange_xml.createElement('EntityIdentifier')
        entity_identifier.setAttribute('code', elements[1])
        entity_identifier.setAttribute('description', entity_identifier_code_map.get(elements[1], 'Unknown Entity Identifier Code'))
        name.appendChild(entity_identifier)
        #party_name
        party_name = self.interchange_xml.createElement('PartyName')
        party_name.setAttribute('value', elements[2])
        name.appendChild(party_name)
        #identification_code
        try:
            id_code = elements[3]
        except IndexError:
            id_code = ""
        identification_code = self.interchange_xml.createElement('IdentificationCode')
        identification_code.setAttribute('qualifier', id_code)
        identification_code.setAttribute('qual_description', identification_code_map.get(id_code, "Unknown Identification Code"))
        name.appendChild(identification_code)
        if this_id == "N1_10":
            self.xml_out_dict['ST_3'].appendChild(party_identification)
        elif this_id == "N1_17":
            self.xml_out_dict['PO1_14'].appendChild(party_identification)
            #self.xml_out_dict['PO1_14'].appendChild(party_identification)
    def do_N3(self, elements, this_id):
        '''<Address addr1="111 Buyer St"/>'''
        address = self.interchange_xml.createElement('Address')
        try:
            addr1 = elements[1]
        except IndexError:
            addr1 = ""
        try:
            addr2 = elements[2]
        except IndexError:
            addr2 = ""
        address.setAttribute('addr1', addr1)
        address.setAttribute('addr2', addr2)
        if this_id == "N3_11":
            self.xml_out_dict["N1_10"].appendChild(address)
        elif this_id == "N3_18":
            self.xml_out_dict["N1_17"].appendChild(address)
    def do_N4(self, elements, this_id):
        '''<GeographicLocation city="Conyers" state="GA" postal_code="30094" country="US"/>'''
        geo_loc = self.interchange_xml.createElement('GeographicLocation')
        try:
            city = elements[1]
        except IndexError:
            city = ""
        try:
            state = elements[2]
        except IndexError:
            state = ""
        try:
            zip_code = elements[3]
        except IndexError:
            zip_code = ""
        try:
            country_code = elements[4]
        except IndexError:
            country_code = ""
        geo_loc.setAttribute('city', city)
        geo_loc.setAttribute('state', state)
        geo_loc.setAttribute('postal_code', zip_code)
        geo_loc.setAttribute('country', country_code)
        if this_id == "N4_12":
            self.xml_out_dict["N1_10"].appendChild(geo_loc)
        elif this_id == "N4_19":
            self.xml_out_dict["N1_17"].appendChild(geo_loc)
    def do_REF(self, elements, this_id):
        '''<ReferenceNumbers qualifier="DP" qual_description="Department Number" number="101" number_description="Swimwear"/>'''
        reference_numbers = self.interchange_xml.createElement('ReferenceNumbers')
        try:
            qual = elements[1]
        except IndexError:
            qual = ""
        qual_descrip = reference_number_qual_map.get(qual, "Unknown Qualifier")
        reference_numbers.setAttribute('qualifier', qual)
        reference_numbers.setAttribute('qual_description', qual_descrip)
        try:
            description = elements[2]
        except IndexError:
            description = ""
        number_descrip = reference_number_map.get(description, "Unknown Qualifier")
        reference_numbers.setAttribute('number_description', number_descrip)
        reference_numbers.setAttribute('number', description)
        if this_id == "REF_13":
            self.xml_out_dict["N1_10"].appendChild(reference_numbers)
        elif this_id == "REF_20":
            self.xml_out_dict["N1_17"].appendChild(reference_numbers)
    def do_PO1(self, elements, this_id):
        '''<LineItem>
        <AssignedId value="100"/>
        <QuantityOrdered value="1"/>
        <Unit code="EA" description="Each"/>
        <ServiceId qualifier="ZZ" qual_description="Mutually Defined" id="BL47"/>
        <ServiceId qualifier="HD" qual_description="Hierarchy Defined" id="100"/>'''
        try:
            assigned_id = elements[1]
        except IndexError:
            assigned_id = ""
        try:
            quantity_ordered = elements[2]
        except IndexError:
            quantity_ordered = ""
        try:
            quantity_ordered = elements[2]
        except IndexError:
            quantity_ordered = ""
        try:
            unit = elements[3]
        except IndexError:
            unit = ""
        try:
            service_id_qual_1 = elements[6]
        except IndexError:
            service_id_qual_1 = ""
        try:
            service_id_1 = elements[7]
        except IndexError:
            service_id_1 = ""
        try:
            service_id_qual_2 = elements[8]
        except IndexError:
            service_id_qual_2 = ""
        try:
            service_id_2 = elements[9]
        except IndexError:
            service_id_2 = ""
        line_item = self.interchange_xml.createElement('LineItem')
        #assigned_id_node
        assigned_id_node = self.interchange_xml.createElement('AssignedId')
        assigned_id_node.setAttribute('value', assigned_id)
        line_item.appendChild(assigned_id_node)
        #quantity_ordered_node
        quantity_ordered_node = self.interchange_xml.createElement('QuantityOrdered')
        quantity_ordered_node.setAttribute('value', quantity_ordered)
        line_item.appendChild(quantity_ordered_node)
        #unit_node
        unit_node = self.interchange_xml.createElement('Unit')
        unit_node.setAttribute('code', unit)
        unit_node.setAttribute('description', unit_code_map.get(unit, 'Unknown Unit Code'))
        line_item.appendChild(unit_node)
        #service_id_node_1
        service_id_node_1 = self.interchange_xml.createElement('ServiceId')
        service_id_node_1.setAttribute('qualifier', service_id_qual_1)
        service_id_node_1.setAttribute('qual_description', service_id_code_map.get(service_id_qual_1, "Unknown Service Id Code Qualifier"))
        service_id_node_1.setAttribute('id', service_id_1)
        line_item.appendChild(service_id_node_1)
        #service_id_node_2
        service_id_node_2 = self.interchange_xml.createElement('ServiceId')
        service_id_node_2.setAttribute('qualifier', service_id_qual_2)
        service_id_node_2.setAttribute('qual_description', service_id_code_map.get(service_id_qual_2, "Unknown Service Id Code Qualifier"))
        service_id_node_2.setAttribute('id', service_id_2)
        line_item.appendChild(service_id_node_2)
        #
        self.xml_out_dict['PO1_14'] = line_item
        self.xml_out_dict['ST_3'].appendChild(line_item)
    def do_PID(self, elements, this_id):
        '''<ProductDescription code="F" code_description="Free Form" description="Widget"/>'''
        try:
            product_description_code = elements[1]
        except IndexError:
            product_description_code = ""
        try:
            product_description = elements[5]
        except IndexError:
            product_description = ""
        #product_description
        product_description_node = self.interchange_xml.createElement('ProductDescription')
        product_description_node.setAttribute('code', product_description_code)
        product_description_node.setAttribute('code_description', product_description_code_map.get(product_description_code, 'Unknown Product Description Code'))
        product_description_node.setAttribute('description', product_description)
        self.xml_out_dict['PO1_14'].appendChild(product_description_node)
    def do_PO4(self, elements, this_id):
        '''<PhysicalDetails size="1" measurement_code="BC"/>'''
        try:
            physical_details_size = elements[2]
        except IndexError:
            physical_details_size = ""
        try:
            measurement_code = elements[3]
        except IndexError:
            measurement_code = ""
        #physical_details_node
        physical_details_node = self.interchange_xml.createElement('PhysicalDetails')
        physical_details_node.setAttribute('size', physical_details_size)
        physical_details_node.setAttribute('measurement_code', measurement_code)
        self.xml_out_dict['PO1_14'].appendChild(physical_details_node)
    def do_CTT(self, elements, this_id):
        try:
            line_item_totals = elements[1]
        except IndexError:
            line_item_totals = ""
        try:
            hash_total = elements[2]
        except IndexError:
            hash_total = ""
        #physical_details_node
        transaction_totals = self.interchange_xml.createElement('TransactionTotals')
        transaction_totals.setAttribute('number_of_line_items', line_item_totals)
        transaction_totals.setAttribute('hash_total', hash_total)
        self.xml_out_dict['ST_3'].appendChild(transaction_totals)
    def do_SE(self, elements, this_id):
        pass
    def do_GE(self, elements, this_id):
        pass
    def do_IEA(self, elements, this_id):
        pass


class NonEDIHandler:
    def __init__(self):
        pass
    def non_edi_data(self, data, begin_fp, end_fp):
        print "*" * 40
        print "NON-EDI Data"
        print "============"
        print "START||%s||END" % data
        print "*" * 40
