import unittest

from parsing.hl7 import mssg_parser
from parsing.hl7 import age_calculator

class TestHL7Parser(unittest.TestCase):

    def test_age_calculator(self):
        """Test age calculation based on date of birth."""

        self.assertEqual(age_calculator("20000101"), 25)  # Born on Jan 1, 2000
        self.assertEqual(age_calculator("19900205"), 35)  # Born on Feb 5, 1990
        self.assertEqual(age_calculator("19851231"), 39)  # Born on Dec 31, 1985
        self.assertEqual(age_calculator("20240306"), 0)   # Born next month (should be 0)

    def test_mssg_parser_adt_a01(self):
        #Test parsing of an ADT^A01 (patient admission) message.
        hl7_msg = b"MSH|^~\&|SIMULATION|SOUTH RIVERSIDE|||202401201630||ADT^A01|||2.5\r" \
                  b"PID|1||478237423||ELIZABETH HOLMES||19900205|F\r" \
                  b"NK1|1|SUNNY BALWANI|PARTNER"
        

        expected_output = ("ADT^A01", ["478237423", 35, "F"]) 
        self.assertEqual(mssg_parser(hl7_msg), expected_output)

    def test_mssg_parser_oru_r01(self):
        #Test parsing of an ORU^R01 (observation result) message.
        hl7_msg = b"MSH|^~\&|SIMULATION|SOUTH RIVERSIDE|||202401201800||ORU^R01|||2.5\r" \
                  b"PID|1||478237423\r" \
                  b"OBR|1||||||202401202243\r" \
                  b"OBX|1|SN|CREATININE||103.4"

        expected_output = ("ORU^R01", ["478237423", 103.4, "202401202243"])
        self.assertEqual(mssg_parser(hl7_msg), expected_output)

    def test_mssg_parser_adt_a03(self):
        #Test parsing of an ADT^A03 (patient discharge) message.
        hl7_msg = b"MSH|^~\&|SIMULATION|SOUTH RIVERSIDE|||202401221000||ADT^A03|||2.5\r" \
                  b"PID|1||478237423"

        expected_output = ("ADT^A03", [])
        self.assertEqual(mssg_parser(hl7_msg), expected_output)

    def test_mssg_parser_ack(self):
        #Test parsing of an ACK (acknowledgment) message.
        hl7_msg = b"MSH|^~\&|||||20240129093837||ACK|||2.5\r" \
                  b"MSA|AA"

        expected_output = ("ACK", [])
        self.assertEqual(mssg_parser(hl7_msg), expected_output)

if __name__ == "__main__":
    unittest.main()
