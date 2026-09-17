
import pandas as pd

# Ground Truth (28 Defects)
GT = {
    "TEST_004": 0, "TEST_008": 1, "TEST_009": 1, "TEST_013": 0, "TEST_014": 1,
    "TEST_015": 1, "TEST_019": 1, "TEST_020": 1, "TEST_023": 1, "TEST_026": 0, 
    "TEST_028": 1, "TEST_029": 1, "TEST_032": 1, "TEST_036": 0, "TEST_042": 1, 
    "TEST_044": 1, "TEST_046": 1, "TEST_047": 1, "TEST_051": 1, "TEST_055": 1, 
    "TEST_057": 0, "TEST_060": 1, "TEST_063": 0, "TEST_068": 1, "TEST_071": 1, 
    "TEST_072": 1, "TEST_076": 1, "TEST_077": 1, "TEST_078": 1, "TEST_082": 1, 
    "TEST_084": 1, "TEST_089": 1, "TEST_094": 0, "TEST_095": 1, "TEST_097": 1, 
    "TEST_098": 1
}

def load_results(path):
    df = pd.read_csv(path)
    return dict(zip(df['id'], df['label']))

v8 = load_results(r"C:\Users\work4\OneDrive\바탕 화면\산업AI_Agnet_해커톤\outpu1t_v8.csv")
v15 = load_results(r"C:\Users\work4\OneDrive\바탕 화면\산업AI_Agnet_해커톤\outpu1t_v15.csv")

print("--- LOST TRUE POSITIVES (Caught by V8, Missed by V15) ---")
lost_tp = []
for id_, label in GT.items():
    if label == 1: # It is a defect
        v8_pred = v8.get(id_, 0)
        v15_pred = v15.get(id_, 0)
        
        if v8_pred == 1 and v15_pred == 0:
            lost_tp.append(id_)
            print(f"{id_}: V8=Defect, V15=Miss")

print(f"\nTotal Lost TPs: {len(lost_tp)}")

print("\n--- SAVED FALSE POSITIVES (V8 Over-flagged, V15 Correctly Ignored) ---")
saved_fp = []
# Iterate all IDs in V8
for id_, v8_pred in v8.items():
    gt_label = GT.get(id_, 0) # Default to 0 if not in list
    v15_pred = v15.get(id_, 0)
    
    if gt_label == 0: # It is Normal
        if v8_pred == 1 and v15_pred == 0:
            saved_fp.append(id_)
            # print(f"{id_}: V8=FP, V15=Correct Normal")

print(f"Total Saved FPs: {len(saved_fp)}")
