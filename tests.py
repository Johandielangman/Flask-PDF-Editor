from pdf import PDF


file1 = "testpdfs/test1"
file2 = "testpdfs/test2"


if __name__ == "__main__":
    # Test encryption
    test1 = PDF(file1+".pdf")
    test1.encrypt("Johan")

    # Test decryption
    test2 = PDF(file1+"_encrypted.pdf")
    test2.decrypt("Johan")

