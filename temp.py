from parsing.hl7 import mssg_parser


def correct_db(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()
        print(len(lines))
        msg = ""
        ans = []
        for l in lines:
            if l[:3] == "MSH":
                ans.append(msg)
                msg = ""
            temp =  l.replace("\n", "\r")
            msg += temp
        ans = ans[1:]
        for m in ans:
            print(mssg_parser(m.encode()))

if __name__ == "__main__":
    correct_db("messages-inc2.txt")