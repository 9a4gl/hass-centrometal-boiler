DOMAIN = "peltec"
PELTEC_CLIENT = "peltec_client"
PELTEC_SYSTEM = "peltec_system"

PELTEC_LOGIN_RETRY_INTERVAL = 60
PELTEC_REFRESH_INTERVAL = 600

PELTEC_KNOWN_ITEMS = []
PELTEC_KNOWN_ITEMS.extend(["B_Tak1_1", "B_Tak2_1", "B_Tdpl1", "B_Tk1", "B_Tpov1"])
PELTEC_KNOWN_ITEMS.extend(["CNT_0", "CNT_1", "CNT_2", "CNT_3", "CNT_4"])
PELTEC_KNOWN_ITEMS.extend(["CNT_5", "CNT_6", "CNT_7", "CNT_8", "CNT_9", "CNT_10"])
PELTEC_KNOWN_ITEMS.extend(["CNT_11", "CNT_12", "CNT_13", "CNT_14", "CNT_15"])
PELTEC_KNOWN_ITEMS.extend(["B_STATE", "B_fan", "B_fanB", "B_Oxy1", "B_FotV", "B_INST"])
PELTEC_KNOWN_ITEMS.extend(["B_sng", "B_VER", "B_WifiVER", "B_PRODNAME", "B_BRAND"])
PELTEC_KNOWN_ITEMS.extend(["PVAL_66_0", "PVAL_67_0", "PVAL_69_0", "PVAL_70_0"])
PELTEC_KNOWN_ITEMS.extend(["PDEF_66_0", "PDEF_67_0", "PDEF_69_0", "PDEF_70_0"])
PELTEC_KNOWN_ITEMS.extend(["PMAX_66_0", "PMAX_67_0", "PMAX_69_0", "PMAX_70_0"])
PELTEC_KNOWN_ITEMS.extend(["PMIN_66_0", "PMIN_67_0", "PMIN_69_0", "PMIN_70_0"])
PELTEC_KNOWN_ITEMS.extend(["B_KONF", "B_vanjS", "B_cm2k", "PVAL_222_0"])
for i in range(223, 226):
    for j in range(0, 42):
        PELTEC_KNOWN_ITEMS.append("PVAL_" + str(i) + "_" + str(j))
PELTEC_KNOWN_ITEMS.extend(["B_razina", "B_misP", "B_Time"])
PELTEC_KNOWN_ITEMS.extend(["B_resDir", "B_resInd", "B_resMax"])
PELTEC_KNOWN_ITEMS.extend(["B_P1", "B_gri", "B_puz"])

"""
0B2D0FDD E22 = P619914DA
0B2D0FDD W1 = N61987B8A

https://www.web-boiler.com/api/template2/template/peltec/peltecdisplay-4-aku?ts=1_0
"""
