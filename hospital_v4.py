import streamlit as st
from datetime import datetime
import matplotlib.pyplot as plt
import os

# setup the page layout
st.set_page_config(page_title="Lifeline", page_icon="🏥", layout="centered")

# css styling for dark mode and specific element looks
st.markdown("""
<style>
.stApp{
    background: linear-gradient(135deg, darkblue, black, maroon);
    font-family:"Segoe UI",sans-serif;
    color:white;
}
h1,h2,h3,h4,h5,h6,p,span,label,div{
    color:white !important;
}
input,textarea,select{
    background-color:black !important;
    color:white !important;
    border-radius:10px !important;
    border:1px solid slategray !important;
}
button{ 
    background-color:steelblue !important;
    border:2px solid indianred !important;
    color:white !important;
}
.bill-box {
    background-color: #222;
    border: 1px solid #FFD700;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# initialize session variables if they dont exist
if "logged" not in st.session_state:
    st.session_state["logged"] = False
if "role" not in st.session_state:
    st.session_state["role"] = ""
if "user" not in st.session_state:
    st.session_state["user"] = ""

# hardcoded file names and admin credentials
usersFile = "Users.txt"
doctorsFile = "Doctors.txt"
adminUsername = "admin"
adminPassword = "admin123"

class LoginError(Exception):
    pass

class ValidationError(Exception):
    pass

# read the file and split by comma. if file crashes, just return empty list
def readFromFile(fileName):
    data = []
    try:
        with open(fileName, "r") as file:
            for line in file:
                data.append(line.strip().split(","))
    except:
        pass
    return data

# append a new line to the file
def writeToFile(fileName, dataLine):
    with open(fileName, "a") as file:
        file.write(dataLine + "\n")

# sidebar login ui
st.title("🏥 LifeLine – Smart Hospital System")
st.sidebar.title("🔐 Secure Login")

# check if user is not logged in
if not st.session_state["logged"]:
    usernameInput = st.sidebar.text_input("Username")
    passwordInput = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login"):
        role = None
        
        # check admin
        if usernameInput == adminUsername and passwordInput == adminPassword:
            role = "Admin"
        
        # check patient login against users file
        elif usernameInput.startswith("pat"):
            patients = readFromFile(usersFile)
            for p in patients:
                # format: id, password, age...
                if len(p) > 1 and p[1] == passwordInput and p[0] == usernameInput:
                    role = "Patient"
                    break
        
        # check doctor login against doctors file
        elif usernameInput.startswith("doc") and usernameInput == passwordInput:
             doctors = readFromFile(doctorsFile)
             for d in doctors:
                 if len(d) > 0 and d[0] == usernameInput:
                     role = "Doctor"
                     break
        
        # if role found, save state and reload
        if role:
            st.session_state["logged"] = True
            st.session_state["role"] = role
            st.session_state["user"] = usernameInput
            st.sidebar.success(f"Welcome {role}!")
            st.rerun() 
        else:
            st.sidebar.error("❌ Invalid Username or Password")

    # stop the script here if not logged in. no peeking
    st.info("👋 Welcome to LifeLine Hospital System")
    st.warning("⚠️ Login first to enter the system 👆")
    st.stop()

# logic for when user is logged in
else:
    st.sidebar.info(f"👤 Logged in as: **{st.session_state['user']}**")
    
    # logout button clears state
    if st.sidebar.button("Logout"):
        st.session_state["logged"] = False
        st.session_state["role"] = ""
        st.session_state["user"] = ""
        st.rerun()

# main application logic starts here
username = st.session_state["user"]
role = st.session_state["role"]

menu = None

# admin menu options
if role == "Admin":
    menu = st.sidebar.selectbox(
        "Control Panel",
        [
            "Add Patient",
            "View Patients",
            "Search Patient",
            "Sort Patients by Age",
            "OPD Queue",
            "Bed Allocation",
            "Add Doctor",
            "Statistics",
        ],
    )
# patient menu options
elif role == "Patient":
    menu = st.sidebar.selectbox(
        "Patient Menu",[           
        "View My Details",
        "Book Appointment", 
        "View Prescriptions",
        "Update Profile",    
        "Medical History",       
        "Discharge & Pay Bill"]
    )
# doctor menu options
elif role == "Doctor":
    menu_options = ["View Appointments", "Add Prescription"]
    default_index = 0
    if "menu" in st.session_state and st.session_state["menu"] in menu_options:
        default_index = menu_options.index(st.session_state["menu"])
    menu = st.sidebar.selectbox("Doctor Menu", menu_options, index=default_index)

# lists and maps for medical data
diseaseList = [
    "Fever", "Cold", "Diabetes", "BP", "Heart Problem", "Asthma", "Infection", "Fracture"
]

doctorSpecializations = [
    "General Physician", "Cardiologist", "Dermatologist", "Neurologist", 
    "Orthopedic", "Pediatrician", "Gynecologist", "ENT", "Psychiatrist"
] 

diseaseDoctorMap = {
    "Fever": "General Physician", "Cold": "General Physician",
    "Diabetes": "General Physician", "BP": "Cardiologist",
    "Heart Problem": "Cardiologist", "Asthma": "General Physician",
    "Infection": "General Physician", "Fracture": "Orthopedic"
}

# find patient in the list
def searchPatient(patientId, patients):
    for p in patients:
        if len(p) > 1 and p[1] == patientId: # checking id at index 1 based on file format
            return p
    return None 

# sort list by age using bubble sort logic
def sortPatientsByAge(patients):
    n = len(patients)
    for i in range(n):
        for j in range(0, n - i - 1):
            try:
                age1 = int(patients[j][2])
                age2 = int(patients[j + 1][2])
                if age1 > age2:
                    patients[j], patients[j + 1] = patients[j + 1], patients[j]
            except: pass
    return patients

if "opdQueue" not in st.session_state:
    st.session_state.opdQueue = []

# pop the first guy from queue
def callNextOpd():
    if len(st.session_state.opdQueue) == 0:
        return "😴 OPD queue is empty. No patients waiting."
    else:
        return st.session_state.opdQueue.pop(0)

# extract all IDs from file
def getAllPatientIds():
    patients = readFromFile(usersFile)
    return [p[0] for p in patients if len(p) > 0] 

if "beds" not in st.session_state:
    st.session_state.beds = {
        "B1": "FREE", "B2": "FREE", "B3": "FREE", "B4": "FREE", "B5": "FREE"
    }

# assign bed if available
def allocateBed(patientId):
    beds = st.session_state.beds
    if patientId in beds.values():
        return "⚠️ Patient already has a bed allocated 😐"
    for bedNo, status in beds.items():
        if status == "FREE":
            timeNow = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            log = (f"\n--- BED ALLOCATED ---\n"
                   f"Bed No: {bedNo}\n"
                   f"Date & Time: {timeNow}\n")
            writeToFile(f"{patientId}.txt", log)
            beds[bedNo] = patientId
            return f"🛏️ Bed {bedNo} successfully allocated to {patientId} ✅"
    return "🚫 All beds are currently full 😴"

# remove patient from bed
def dischargeBed(patientId):
    beds = st.session_state.beds
    for bedNo, status in beds.items():
        if status == patientId:
            beds[bedNo] = "FREE"
            timeNow = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            log = (f"\n--- BED DISCHARGED ---\n"
                   f"Bed No: {bedNo}\n"
                   f"Date & Time: {timeNow}\n")
            writeToFile(f"{patientId}.txt", log)
            return f"🛏️ {patientId} discharged from {bedNo} successfully"
    return "❌ Patient not found in any bed 😐"

# scan text file for keywords to calculate money
def calculateBill(patientId):
    total = 0
    breakdown = []
    
    try:
        with open(f"{patientId}.txt", "r") as file:
            for line in file:
                line = line.strip()
                if "Registration fees:" in line:
                    try:
                        amt = int(line.split(":")[1].strip())
                        total += amt
                        breakdown.append(f"Registration Fee: Rs. {amt}")
                    except: pass
                
                if "Appointment Fee:" in line:
                    try:
                        amt = int(line.split(":")[1].strip())
                        total += amt
                        breakdown.append(f"Appointment Charge: Rs. {amt}")
                    except: pass
                
                if "PAYMENT MADE:" in line:
                    try:
                        amt = int(line.split(":")[1].strip())
                        total -= amt
                        breakdown.append(f"Less Payment: -Rs. {amt}")
                    except: pass
    except FileNotFoundError:
        pass

    bedFee = 300 
    inBed = False
    currentBed = ""
    
    for bed, occupant in st.session_state.beds.items():
        if occupant == patientId:
            total += bedFee
            breakdown.append(f"Current Bed Charge ({bed}): Rs. {bedFee}")
            inBed = True
            currentBed = bed
            break
            
    return total, breakdown, inBed, currentBed

# start of menu handling

if menu == "Add Patient":
    st.subheader("➕ Add New Patient 🧑‍⚕️")
    st.info("Please fill all details to register a new patient.")

    # layout for inputs
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Patient Name")
        age = st.number_input("Age", min_value=0, max_value=100, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    
    with col2:
        contact = st.text_input("Contact Number", max_chars=10)
        bloodGroup = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        address = st.text_area("Address", height=100)
    disease = st.multiselect("Diseases/Symptoms", diseaseList)

    # auto create id
    patientId = ""
    if name and age:
        patientId = "pat" + name[:3].lower() + str(age)

    if st.button("Save Patient"):
        try:
            # check inputs
            if not name or not contact or not address:
                raise ValidationError("❌ All fields (Name, Contact, Address) are required.")
            
            if not name.replace(" ", "").isalpha():
                raise ValidationError("❌ Name must contain letters only.")
                
            if age <= 0:
                raise ValidationError("❌ Age must be greater than 0.")
                
            if not contact.isdigit() or len(contact) != 10:
                raise ValidationError("❌ Contact number must be exactly 10 digits.")

            # check for duplicates
            try:
                currentUsers = readFromFile(usersFile)
                for u in currentUsers:
                    if len(u) > 0 and u[0] == patientId:
                        raise ValidationError("⚠️ Patient ID conflict! Try adding middle name or changing format.")
            except FileNotFoundError:
                pass
            
            # create password key
            passKey = name.split()[0] + "@" + str(age)
            
            # save to master file
            # format: patientId, password, age, name, contact
            writeToFile(usersFile, f"{patientId},{passKey},{age},{name},{contact}")

            # save detailed info to individual file
            patientDetails = (
                f"Patient ID: {patientId}\n"
                f"Name: {name}\n"
                f"Age: {age}\n"
                f"Gender: {gender}\n"
                f"Blood Group: {bloodGroup}\n"
                f"Contact: {contact}\n"
                f"Address: {address}\n"
                f"Diseases: {', '.join(disease) if disease else 'None'}\n"
                f"Registration Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"------------------------------\n"
                f"Registration fees: 1000  \n"
            )

            writeToFile(f"{patientId}.txt", patientDetails)
            
            st.success(f"✅ Patient Registered Successfully!")
            st.info(f"🆔 **Patient ID:** {patientId} (Use this as Username)")
            st.info(f"🔑 **Password:** {passKey}")

        except ValidationError as e:
            st.error(e)

elif menu == "View Patients":
    st.subheader("📋 Registered Patients")
    patients = readFromFile(usersFile)
    if not patients:
        st.warning("No patients found.")
    else:
        # Sort patients by registration time (newest first)
        patient_details = []
        for p in patients:
            if len(p) > 3:
                pid = p[0]
                name = p[3]
                age = p[2]
                contact = p[4] if len(p) > 4 else "N/A"
                reg_time = "N/A"
                try:
                    with open(f"{pid}.txt", "r") as file:
                        for line in file:
                            if "Registration Time:" in line:
                                reg_time = line.split("Registration Time:")[1].strip()
                                break
                except:
                    pass
                patient_details.append((pid, name, age, contact, reg_time))
        
        # Sort by registration time (assuming format YYYY-MM-DD HH:MM:SS)
        try:
            patient_details.sort(key=lambda x: x[4] if x[4] != "N/A" else "0000-00-00 00:00:00", reverse=True)
        except:
            pass
        
        for pid, name, age, contact, reg_time in patient_details:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"🧑 **ID:** `{pid}` | **Name:** {name} | **Age:** {age} | 📞 {contact}")
                    st.caption(f"📅 Registered: {reg_time}")
                with col2:
                    if st.button("View Full Details", key=f"view_{pid}"):
                        try:
                            with open(f"{pid}.txt", "r") as f:
                                details = f.read()
                            st.text_area("Patient Details", details, height=250, key=f"details_{pid}")
                        except:
                            st.error("Details not available")
                st.markdown("---")

elif menu == "Search Patient":
    pid = st.selectbox("Select Patient ID to Search", getAllPatientIds())
    if st.button("Search"):
        # search by id at index 0
        result = None
        patients = readFromFile(usersFile)
        for p in patients:
            if len(p) > 0 and p[0] == pid:
                result = p
                break
                
        if result:
            st.success(f"Found: {result[3]}")
            # show full file if exists
            if os.path.exists(f"{pid}.txt"):
                with open(f"{pid}.txt", "r") as f:
                    st.text(f.read())
            else:
                st.write(f"Basic Info: Name: {result[3]}, Age: {result[2]}")
        else:
            st.error("❌ Patient not found 😐")

elif menu == "Sort Patients by Age":
    patients = sortPatientsByAge(readFromFile(usersFile))
    for p in patients:
        if len(p) > 3:
            st.write(f"🧑 ID: {p[0]} | Name: {p[3]} | Age: {p[2]}")
        st.write("---")

elif menu == "OPD Queue":   
    st.subheader("🧾 OPD Waiting List")
    patientIds = getAllPatientIds()
    if not patientIds:
        st.warning("⚠️ No patients available right now 😐")
    else:
        pid = st.selectbox("Choose Patient ID", patientIds)
        if st.button("Add to OPD"):
            st.session_state.opdQueue.append(pid)
            st.success(f"🧾 {pid} added to OPD queue ✅")
        st.info(f"📋 Current Queue: {st.session_state.opdQueue}")
        if st.button("Call Next"):
            st.info(callNextOpd())

elif menu == "Bed Allocation":
    st.subheader("🛏️ Bed Management")
    patientIds = getAllPatientIds()
    if not patientIds:
        st.warning("⚠️ No patients found 😐")
    else:
        pid = st.selectbox("Select Patient ID", patientIds)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Allocate Bed"):
                st.success(allocateBed(pid))
        with col2:
            if st.button("Discharge Patient"):
                st.info(dischargeBed(pid))
    st.subheader("📊 Live Bed Status")
    st.write(st.session_state.beds)

elif menu == "Add Doctor":
    st.subheader("👨‍⚕️ Add Doctor Profile")
    st.info("Enter professional details to register a doctor.")

    col1, col2 = st.columns(2)
    
    with col1:
        dname = st.text_input("Doctor Name")
        age = st.number_input("Age", min_value=25, max_value=80, step=1)
        gender = st.selectbox("Gender", ["Male", "Female"])
        spec = st.selectbox("Specialization", doctorSpecializations)
        
    with col2:
        qualification = st.text_input("Qualification (e.g., MBBS, MD)")
        experience = st.number_input("Experience (Years)", min_value=0, step=1)
        contact = st.text_input("Contact Number", max_chars=10)

    did = ""
    if dname.strip():
        did = "doc" + dname.strip().replace(" ", "")[:3].lower() + str(age)

    if st.button("Add Doctor"):
        try:
            # validate doctor inputs
            if not dname or not qualification or not contact:
                raise ValidationError("❌ Name, Qualification, and Contact are required.")
            
            if not dname.replace(" ", "").isalpha():
                raise ValidationError("❌ Doctor name should contain only letters.")
            
            if not contact.isdigit() or len(contact) != 10:
                raise ValidationError("❌ Contact number must be 10 digits.")

            doctors = readFromFile(doctorsFile)
            existingIds = [d[0] for d in doctors if len(d)>0]
            
            if did in existingIds:
                raise ValidationError("⚠️ Doctor already exists in system.")

            # save doctor data
            dataLine = f"{did},{dname},{spec},{gender},{qualification},{experience} yrs,{contact}"
            writeToFile(doctorsFile, dataLine)
            
            st.success(f"👨‍⚕️ Doctor added successfully! ✅")
            st.info(f"🆔 **Doctor ID:** {did}")

        except ValidationError as e:
            st.error(e)


elif menu == "Statistics":
    st.subheader("📈 Hospital Insights")

    patients = readFromFile("Users.txt")
    if not patients:
        st.warning("⚠️ No patient data available 😐")
        st.stop()

    ages = [int(p[2]) for p in patients]
    st.info(f"👥 Total Patients Registered: {len(patients)}")
    st.success(f"📊 Average Patient Age: {sum(ages)//len(ages)} years")

    age_groups = {
        "0-10": 0, "11-20": 0, "21-30": 0,
        "31-40": 0, "41-50": 0, "51-60": 0, "61+": 0
    }

    for age in ages:
        if age <= 10: age_groups["0-10"] += 1
        elif age <= 20: age_groups["11-20"] += 1
        elif age <= 30: age_groups["21-30"] += 1
        elif age <= 40: age_groups["31-40"] += 1
        elif age <= 50: age_groups["41-50"] += 1
        elif age <= 60: age_groups["51-60"] += 1
        else: age_groups["61+"] += 1

    st.bar_chart(age_groups)

    diseaseCount = {}
    for p in patients:
        pid = p[0]
        try:
            with open(f"{pid}.txt", "r") as file:
                for line in file:
                    if line.startswith("Diseases:"):
                        diseases = line.replace("Diseases:", "").strip().split(",")
                        for d in diseases:
                            diseaseCount[d.strip()] = diseaseCount.get(d.strip(), 0) + 1
        except:
            pass

    if diseaseCount:
        st.info(f"🦠 Total Disease Types Recorded: {len(diseaseCount)}")
        st.bar_chart(diseaseCount)
    else:
        st.warning("⚠️ No disease data found 😐")

elif menu == "View My Details":
    st.subheader("👤 My Patient Details")
    patientData = ""
    try:
        with open(f"{username}.txt", "r") as file:
            patientData = file.read()
        st.text(patientData)
        st.download_button(
            label="📥 Download My Details",
            data=patientData,
            file_name=f"{username}_details.txt",
            mime="text/plain"
        )
    except FileNotFoundError:
        st.error("❌ No details found for your account 😐"  )

elif menu == "Book Appointment":
    st.subheader("📅 Book Appointment")
    disease = st.multiselect("Select Symptoms/Disease", diseaseList)
    
    if disease:
        charges = {
            "Fever": 100, "Cold": 50, "Diabetes": 150, 
            "BP": 150, "Heart Problem": 500, "Asthma": 200, 
            "Infection": 100, "Fracture": 300
        }
        totalConsultation = sum([charges.get(d, 100) for d in disease])
        
        st.info(f"🏥 Estimated Consultation Fee: Rs. {totalConsultation}")

        if st.button("Confirm Booking"):
            assignedDocs = []
            doctors = readFromFile(doctorsFile)
            for d in disease:
                spec = diseaseDoctorMap.get(d, "General Physician")
                # Find actual doctor names with this specialization
                doc_names = [doc[1] for doc in doctors if len(doc) > 2 and doc[2] == spec]
                if doc_names:
                    assignedDocs.append(doc_names[0])  # Assign the first available doctor
                else:
                    assignedDocs.append(spec)  # Fallback to specialization if no doctor found
            
            assignedDocs = list(set(assignedDocs))  # Remove duplicates
            
            st.success(f"✅ Appointment booked with: {', '.join(assignedDocs)} 🎉")
            
            log = (f"\n--- APPOINTMENT BOOKED ---\n"
                   f"Diseases: {', '.join(disease)}\n"
                   f"Doctors: {', '.join(assignedDocs)}\n"
                   f"Date & Time: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n")
            writeToFile(f"{username}.txt", log)
            writeToFile(f"{username}.txt", f"Appointment Fee: {totalConsultation}")

elif menu == "View Prescriptions":
    st.subheader("💊 My Prescriptions")
    prescriptions = ""
    try:
        with open(f"{username}.txt", "r") as file:
            for line in file:
                if "Prescription:" in line:
                    prescriptions += line + "\n"
        if prescriptions:
            st.text(prescriptions)
        else:
            st.warning("⚠️ No prescriptions found yet.")
    except FileNotFoundError:
        st.error("❌ No records found.")

elif menu == "Discharge & Pay Bill":
    st.subheader("💸 Discharge & Payment Portal")
    
    totalAmount, breakdown, isInBed, bedNo = calculateBill(username)
    
    col1, col2 = st.columns([1,1])
    
    with col1:
        st.markdown('<div class="bill-box">', unsafe_allow_html=True)
        st.markdown("### 🧾 Bill Summary")
        if not breakdown and totalAmount == 0:
            st.write("✅ No outstanding dues.")
        else:
            for item in breakdown:
                st.write(f"🔹 {item}")
            st.markdown("---")
            st.markdown(f"### 💰 Total Payable: Rs. {totalAmount}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("### 💳 Payment Gateway")
        
        if totalAmount > 0:
            payMethod = st.radio("Select Payment Method:", ["💳 Debit/Credit Card", "📱 UPI / QR Code"], horizontal=True)
            st.write("---")
            
            if payMethod == "💳 Debit/Credit Card":
                st.write("Enter details to process discharge:")
                cardName = st.text_input("Cardholder Name")
                cardNum = st.text_input("Card Number", type="password", max_chars=16)
                cvv = st.text_input("CVV", type="password",max_chars=4)
                
                if st.button(f"Pay Rs. {totalAmount}"):
                    if cardName and cardNum:
                        log = (f"\n--- PAYMENT RECEIPT ---\n"
                               f"Date: {datetime.now()}\n"
                               f"Method: Card\n"
                               f"PAYMENT MADE: {totalAmount}\n"
                               f"Status: Success\n")
                        writeToFile(f"{username}.txt", log)
                        
                        if isInBed:
                            st.session_state.beds[bedNo] = "FREE"
                            writeToFile(f"{username}.txt", f"--- DISCHARGED FROM {bedNo} ---\n")
                        
                        st.success("✅ Payment Successful! You are discharged.")
                        st.rerun()
                    else:
                        st.error("⚠️ Please enter dummy card details.")

            elif payMethod == "📱 UPI / QR Code":
                st.info(f"Scan QR to pay **Rs. {totalAmount}**")
                st.image("qr.png ")
                if st.button("✅ I have paid"):
                    log = (f"\n--- PAYMENT RECEIPT ---\n"
                           f"Date: {datetime.now()}\n"
                           f"Method: UPI\n"
                           f"PAYMENT MADE: {totalAmount}\n"
                           f"Status: Success\n")
                    writeToFile(f"{username}.txt", log)
                    
                    if isInBed:
                        st.session_state.beds[bedNo] = "FREE"
                        writeToFile(f"{username}.txt", f"--- DISCHARGED FROM {bedNo} ---\n")
            
                    st.success("✅ Payment Verified! You are discharged.")
                    st.rerun()

        elif totalAmount == 0 and isInBed:
            if st.button("Discharge (No Dues)"):
                st.session_state.beds[bedNo] = "FREE"
                writeToFile(f"{username}.txt", f"--- DISCHARGED FROM {bedNo} ---\n")
                st.success(f"✅ Discharged from {bedNo}.")
                st.rerun()
        elif totalAmount < 0:
            st.info("ℹ️ You have credit balance.")

elif menu == "Update Profile":
    st.subheader("📝 Update My Profile")
    st.info("Update your contact information and address.")

    # Read current details
    current_contact = ""
    current_address = ""
    try:
        with open(f"{username}.txt", "r") as file:
            for line in file:
                if line.startswith("Contact:"):
                    current_contact = line.split("Contact:")[1].strip()
                elif line.startswith("Address:"):
                    current_address = line.split("Address:")[1].strip()
    except:
        pass

    col1, col2 = st.columns(2)
    with col1:
        new_contact = st.text_input("Contact Number", value=current_contact, max_chars=10)
    with col2:
        new_address = st.text_area("Address", value=current_address, height=100)

    if st.button("Update Profile"):
        try:
            if not new_contact or not new_address:
                st.error("❌ Contact and Address are required.")
            elif not new_contact.isdigit() or len(new_contact) != 10:
                st.error("❌ Contact number must be 10 digits.")
            else:
                # Read the entire file
                with open(f"{username}.txt", "r") as file:
                    lines = file.readlines()
                
                # Update the lines
                with open(f"{username}.txt", "w") as file:
                    for line in lines:
                        if line.startswith("Contact:"):
                            file.write(f"Contact: {new_contact}\n")
                        elif line.startswith("Address:"):
                            file.write(f"Address: {new_address}\n")
                        else:
                            file.write(line)
                
                # Also update in Users.txt
                patients = readFromFile(usersFile)
                with open(usersFile, "w") as file:
                    for p in patients:
                        if len(p) > 0 and p[0] == username:
                            p[4] = new_contact  # assuming contact is at index 4
                        file.write(",".join(p) + "\n")
                
                st.success("✅ Profile updated successfully!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error updating profile: {e}")

elif menu == "Medical History":
    st.subheader("📚 My Medical History")
    st.info("Summary of your medical activities.")

    history = {
        "Appointments": [],
        "Prescriptions": [],
        "Bed Allocations": [],
        "Payments": []
    }

    try:
        with open(f"{username}.txt", "r") as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if "--- APPOINTMENT BOOKED ---" in line:
                    try:
                        diseases = lines[i+1].strip().replace("Diseases: ", "")
                        doctors = lines[i+2].strip().replace("Doctors: ", "")
                        date_time = lines[i+3].strip().replace("Date & Time: ", "")
                        history["Appointments"].append(f"{date_time}: {diseases} - Dr. {doctors}")
                    except:
                        pass
                elif "--- PRESCRIPTION ADDED ---" in line:
                    try:
                        doctor = lines[i+1].strip().replace("Doctor ID: ", "")
                        prescription = lines[i+2].strip().replace("Prescription: ", "")
                        date_time = lines[i+3].strip().replace("Date & Time: ", "")
                        history["Prescriptions"].append(f"{date_time}: {prescription} (Dr. {doctor})")
                    except:
                        pass
                elif "--- BED ALLOCATED ---" in line:
                    try:
                        bed = lines[i+1].strip().replace("Bed No: ", "")
                        date_time = lines[i+2].strip().replace("Date & Time: ", "")
                        history["Bed Allocations"].append(f"{date_time}: Allocated to {bed}")
                    except:
                        pass
                elif "--- PAYMENT RECEIPT ---" in line:
                    try:
                        method = lines[i+2].strip().replace("Method: ", "")
                        amount = lines[i+3].strip().replace("PAYMENT MADE: ", "")
                        date = lines[i+1].strip().replace("Date: ", "")
                        history["Payments"].append(f"{date}: Rs. {amount} via {method}")
                    except:
                        pass

    except FileNotFoundError:
        st.error("❌ No medical history found.")

    for category, items in history.items():
        if items:
            st.subheader(f"📋 {category}")
            for item in items:
                st.write(f"• {item}")
            st.markdown("---")
        else:
            st.write(f"📋 {category}: None")

elif menu == "View Appointments":
    st.subheader("📅 Doctor's Appointments")
    
    doctors = readFromFile(doctorsFile)
    mySpec = ""
    myName = ""
    
    for doc in doctors:
        if len(doc) > 0 and doc[0] == username:
            myName = doc[1]
            mySpec = doc[2]
            break
            
    if not mySpec:
        st.error("❌ Doctor profile not found.")
    else:
        st.info(f"👨‍⚕️ Welcome Dr. {myName} ({mySpec})")
        
        patients = readFromFile(usersFile)
        foundAny = False

        for p in patients:
            if len(p) > 1:
                pid = p[0] 
                pname = p[3]
                try:
                    with open(f"{pid}.txt", "r") as file:
                        lines = file.readlines()
                        for i in range(len(lines)):
                            if "--- APPOINTMENT BOOKED ---" in lines[i]:
                                try:
                                    docLine = lines[i+2].strip() 
                                    if myName in docLine: 
                                        with st.container():
                                            st.markdown(f"**👤 {pname}** (`{pid}`)")
                                            st.caption("Has booked an appointment.")
                                            if st.button("Mark Treated", key=f"btn_{pid}_{i}"):
                                                st.session_state["menu"] = "Add Prescription"
                                                st.session_state["prescribe_patient"] = pid
                                                st.success("Patient marked as treated. Switching to Add Prescription...")
                                                st.rerun()
                                            st.markdown("---")
                                        foundAny = True
                                except: pass
                except: pass

        if not foundAny:
            st.warning("📭 No appointments found.")

elif menu == "Add Prescription":
    st.subheader("💊 Add Prescription")
    
    if "prescribe_patient" in st.session_state:
        pId = st.text_input("Patient ID", value=st.session_state["prescribe_patient"])
        st.info("💡 Patient ID pre-filled from treated appointment.")
    else:
        patients = readFromFile(usersFile)
        patientOptions = {f"{p[0]} - {p[3]}": p[0] for p in patients if len(p) > 3}
        selected = st.selectbox("Select Patient ID with Name", list(patientOptions.keys()))
        pId = patientOptions[selected]
    
    prescriptionText = st.text_area("Prescription Details")
    
    if st.button("Add Prescription"):
        if not pId or not prescriptionText:
             st.warning("⚠️ Please enter both Patient ID and Prescription details.")
        else:
            if os.path.exists(f"{pId}.txt"):
                with open(f"{pId}.txt", "a") as file:
                    log = (f"\n--- PRESCRIPTION ADDED ---\n"
                           f"Doctor ID: {username}\n"
                           f"Prescription: {prescriptionText}\n"
                           f"Date & Time: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n")
                    file.write(log)
                st.success("✅ Prescription added successfully 🎉")
                if "prescribe_patient" in st.session_state:
                    st.session_state["menu"] = "View Appointments"
                    del st.session_state["prescribe_patient"]
                    st.info("🔄 Returning to View Appointments...")
                st.rerun()
            else:
                st.error("❌ Patient ID not found in database 😐")