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


"""

0B2D0FDD B_P1 = 0 -
0B2D0FDD B_gri = 0 - Heater 0/1
0B2D0FDD B_puz = 0 - pu�nica za pelet?

0B2D0FDD B_ashC = 0
0B2D0FDD B_addConf = 0
0B2D0FDD B_ashSc = 0
0B2D0FDD B_bcl = 0
0B2D0FDD B_bim = 0
0B2D0FDD B_bup = 1
0B2D0FDD B_CMD = 0
0B2D0FDD B_dop = 0
0B2D0FDD B_doz = 0
0B2D0FDD B_fanO = 0
0B2D0FDD B_fireS = 0
0B2D0FDD B_HS_AKU = 0
0B2D0FDD B_Inp1 = 28
0B2D0FDD B_korNum = 255
0B2D0FDD B_Mpc = 0
0B2D0FDD B_Mpo = 0
0B2D0FDD B_Out1 = 0
0B2D0FDD B_P2 = 0
0B2D0FDD B_P3 = 0
0B2D0FDD B_pres = 1
0B2D0FDD B_puzOff = 0
0B2D0FDD B_puzOffO = 0
0B2D0FDD B_puzOn = 0
0B2D0FDD B_puzOnO = 0
0B2D0FDD B_razP = 0
0B2D0FDD B_REC = 0
0B2D0FDD B_REO = 0
0B2D0FDD B_rpm = 0
0B2D0FDD B_signal = 57
0B2D0FDD B_sob = 0
0B2D0FDD B_sob2 = 0
0B2D0FDD B_specG = 0
0B2D0FDD B_start = 0
0B2D0FDD B_StsB1 = 9
0B2D0FDD B_StsN1 = 200
0B2D0FDD B_SUP_TYPE = 2
0B2D0FDD B_Ths1 = 50
0B2D0FDD B_Tkm1 = -55
0B2D0FDD B_Tptv1 = -55
0B2D0FDD B_tur = 0
0B2D0FDD B_Tva1 = -55
0B2D0FDD B_zahP1 = 1
0B2D0FDD B_zahP2 = 0
0B2D0FDD B_zahP3 = 0
0B2D0FDD B_zatPTV = 0
0B2D0FDD B_zatRad = 0
0B2D0FDD CMD_TIME = 0
0B2D0FDD PING = 10932
0B2D0FDD SE00 = 0
0B2D0FDD SE01 = 0
0B2D0FDD SE02 = 0
0B2D0FDD wf_req = ?

0B2D0FDD E22 = P619914DA
0B2D0FDD W1 = N61987B8A

https://www.web-boiler.com/api/template2/template/peltec/peltecdisplay-4-aku?ts=1_0
"""
