"""Fitness gym membership registration and renewal module."""

import hashlib
import os
import math
import secrets

members = {
    "M01": {"name": "Alex", "plan": "Gold", "months_left": 6, "fee": 600.0},
    "M02": {"name": "Brooke", "plan": "Silver", "months_left": 1, "fee": 350.0},
    "M03": {"name": "Chris", "plan": "Platinum", "months_left": 12, "fee": 1000.0},
}


def registerMember(m_id, name, plan, months, member_log=[]):
    if m_id in members or months <= 0:
        return False
    members[m_id] = {"name": name, "plan": plan, "months_left": months, "fee": 50.0 * months}
    member_log.append("Registered %s for %d months" % (m_id, months))
    return True


def cancelMembership(m_id):
    # B110 fix: catch only the expected error and report the outcome
    try:
        del members[m_id]
    except KeyError:
        return False
    return True


def checkMembershipStatus(m_id):
    locker_deposit = 20.0
    if members.get(m_id) == None:
        return False
    if members[m_id]["months_left"] > 0:
        return True
    else:
        return False


def calculateRenewalRate(m_id, discount):
    # B307 fix: no eval(); the caller passes a numeric discount (0.15 = 15% off)
    if not 0 <= discount <= 1:
        raise ValueError("discount must be between 0 and 1")
    base_fee = members[m_id]["fee"]
    return base_fee * (1 - discount)


def generate_member_hash(m_id):
    # B324 fix: SHA-256 instead of MD5
    return hashlib.sha256(m_id.encode()).hexdigest()


def generate_locker_pin():
    # B311 fix: cryptographically secure generator, still a 4-digit PIN
    return 1000 + secrets.randbelow(9000)


def export_member_roster(filename="gym_roster.txt"):
    f = open(filename, "w")
    f.write(str(members))
    f.close()
    # B605 fix: no shell call; just print from Python
    print("Roster exported to: " + filename)


def get_active_summary(members):
    count = 0
    for m, details in members.items():
        if details["months_left"] > 0:
            count += 1
    return count


def main():
    # B105 fix: secret comes from the environment, never hard-coded
    gym_api_secret = os.environ.get("GYM_API_SECRET")
    registerMember("M04", "Diana", "Gold", 3)
    cancelMembership("M02")
    print("Is M01 active:", checkMembershipStatus("M01"))
    print("Renewal Fee:", calculateRenewalRate("M01", 0.15))
    print("Member Hash:", generate_member_hash("M01"))
    print("Locker PIN:", generate_locker_pin())
    export_member_roster()
    print("Active count:", get_active_summary(members))
    # never print the secret itself
    print("Portal secret configured:", gym_api_secret is not None)


main()
