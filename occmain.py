print("Optimistic Concurrency Control\n")
print("=="*15)
filename=str(input("Input nama file: "))

# baca file
if not filename:
    filename = "test.txt"

file = open(filename, "r")

# parse file jadi records
text = list(file)
records = [t.strip() for t in text]
in_trans = ""
for i in range(len(records)):
    in_trans += records[i] + "; "
    
# record reverse supaya bisa pop
records.reverse()

transactions = {}

# fungsi intersect
def intersect(arr1, arr2):
    return list(set(arr1) & set(arr2))

timestamp = 1
while len(records) > 0:
    current = records.pop()
    trx = int(current[1])
    
    # set current component
    curr_comp = ["", "", ""]
    curr_comp[0] = trx
    curr_comp[1] = current[0]
    
    
    # check trx not in transactions
    if trx not in transactions.keys():
        transactions[trx] = {
            "Start": timestamp,
            "Validation": 0,
            "Finish": 0,
            "Result": None,
            "Read": [],
            "Write": []
        }

    #commit
    if current[0] != "C":
        curr_comp[2] = current[3]

    # start
    if curr_comp[1] == "R":
        if curr_comp[2] not in transactions[curr_comp[0]]["Read"]:
            transactions[curr_comp[0]]["Read"].append(curr_comp[2])
    elif curr_comp[1] == "W":
        if curr_comp[2] not in transactions[curr_comp[0]]["Write"]:
            transactions[curr_comp[0]]["Write"].append(curr_comp[2])

    # validasi
    if curr_comp[1] == "C":
        transactions[curr_comp[0]]["Validation"] = timestamp
        result = "berhasil"
        for key in transactions.keys():
            transaction = transactions[key]
            if (
                transaction["Validation"] != 0
                and transaction["Validation"] < transactions[curr_comp[0]]["Validation"]
            ):
                if transaction["Finish"] < transactions[curr_comp[0]]["Start"]:
                    result = "berhasil"
                else:
                    intersected = intersect(transaction["Write"], transactions[curr_comp[0]]["Read"])
                    if transaction["Finish"] < timestamp and len(intersected) == 0:
                        result = "berhasil"
                    else:
                        result = f"intersect antara transaksi {curr_comp[0]} dengan transaksi {key} pada saat pembacaan data {intersected}"
                        break
        transactions[curr_comp[0]]["Result"] = result

        # finish
        transactions[curr_comp[0]]["Finish"] = timestamp if transactions[curr_comp[0]]["Result"] == "berhasil" else -1

    timestamp += 1

print(f"Transaksi Input : {in_trans}\n")

for key in transactions.keys():
    transaction = transactions[key]
    message = transaction["Result"]
    success = "    Start = " + str(transaction["Start"]) + "\n    Validation = " + str(transaction["Validation"]) + "\n    Finish = " + str(transaction["Finish"])
    
    if transaction["Result"] == "berhasil":
        hasil = "success:\n" + success
    else:
        hasil = "failed: " + message  
        
    print(f"Transaksi {key} {hasil}\n")