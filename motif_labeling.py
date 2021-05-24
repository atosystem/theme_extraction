
from miditoolkit.midi import parser as mid_parser
from miditoolkit.midi import containers as ct
import copy
from LCS import lcs


def group_ticks(note_items):
    _note_items = copy.deepcopy(note_items)
    _note_items.sort(key=lambda x: (x.start, x.pitch))
    notes_grp = []
    current_grp = {
        "idx" : 0,
        "start" : _note_items[0].start,
        "notes" : [_note_items[0]]
    }
    g_idx = 0
    for i,n in enumerate(_note_items[1:]):
        if n.start == current_grp["notes"][-1].start:
            if n.end == current_grp["notes"][-1].end and n.pitch == current_grp["notes"][-1].pitch:
                continue
            current_grp["notes"].append(n)
        else:
            notes_grp.append(current_grp)
            g_idx += 1
            current_grp = {
                "idx" : g_idx,
                "start" : n.start,
                "notes" : [n]
            }

    if not len(current_grp) == 0:
        notes_grp.append(current_grp)
    
    return notes_grp

   
def motif_LCS(motif_notes_grp,full_song_notes_grp,param=None,verbose = False):
    if param == None:
        param = {
            "distance_threshold" : 1000,
            "min_len" : 5,
            "pitch_shift" : False,
            "chroma" : False,
            "reverse" : False,
            "mirror" : False
        }
    
    # Function for recursion
    def split_find(motif_notes_grp_part,full_notes_grp_part,selected_list,verbose = False):
        if len(full_notes_grp_part) <= param["min_len"]:
            return
        m_A , m_B, matched_notes_count = lcs(motif_notes_grp_part,full_notes_grp_part,my_equal_func,
            param["distance_threshold"],
            input_A_ticks_per_beat=param["input_A_ticks_per_beat"],
            input_B_ticks_per_beat=param["input_B_ticks_per_beat"],
            verbose=verbose)

        if matched_notes_count >= param["min_len"]:
            
            # print("motif",[motif_notes_grp_part[x]["idx"] for x in m_A])
            entry = []
            
            for x in m_B:
                entry.append(full_notes_grp_part[x]["idx"])

            selected_list.append([[motif_notes_grp_part[x]["idx"] for x in m_A],entry])

            split_find(motif_notes_grp_part,full_notes_grp_part[0:m_B[0]],selected_list,verbose=verbose)
            split_find(motif_notes_grp_part,full_notes_grp_part[m_B[-1]+1:],selected_list,verbose=verbose)
 
    
    total_selected_idx = {}
    
    # define match function
    if param["chroma"]:
        def my_equal_func(a,b):
            total_matched = 0
            for n_a in a["notes"]:
                for n_b in b["notes"]:
                    if n_a.pitch%12 == n_b.pitch%12:
                        total_matched += 1
                        break
            return  total_matched
    
    else:
        def my_equal_func(a,b):
            total_matched = 0
            for n_a in a["notes"]:
                for n_b in b["notes"]:
                    if n_a.pitch == n_b.pitch:
                        total_matched += 1
                        break
            return  total_matched

    # do variations on motif
    motif_notes_grp_alter = copy.deepcopy(motif_notes_grp)
    if param["reverse"]:
        max_tick = 0
        for n in motif_notes_grp_alter[-1]["notes"]:
            max_tick = max(max_tick,n.start)
        
        for g in motif_notes_grp_alter:
            g["start"] = -g["start"] + max_tick
            # g["idx"] = -g["idx"] + len(motif_notes_grp_alter) - 1

        motif_notes_grp_alter.sort(key=lambda x: (x["start"]))

    if param["mirror"]:
        top_line = 0
        for g in motif_notes_grp_alter:
            for n in g["notes"]:
                top_line = max(top_line,n.pitch)

        # flip the notes
        for g in motif_notes_grp_alter:
            for n in g["notes"]:
                n.pitch = 2 * top_line - n.pitch
        
    # method for searching
    if param["pitch_shift"]:
        
        selected_idx = []
        max_pitch = 0
        min_pitch = 128
        for grp in motif_notes_grp_alter:
            for n in grp["notes"]:
                max_pitch = max(max_pitch,n.pitch)
                min_pitch = min(min_pitch,n.pitch)
        
        for pitch_shift in range(0-min_pitch,128-max_pitch):
        # for pitch_shift in range(-6,6):
            motif_notes_grp_offset = copy.deepcopy(motif_notes_grp_alter)
            for grp in motif_notes_grp_offset:
                for n in grp["notes"]:
                    n.pitch += pitch_shift

            split_find(motif_notes_grp_offset,full_song_notes_grp,selected_idx,verbose=verbose)
        total_selected_idx["pitch_shift"] = selected_idx

    else:
        selected_idx = []
        split_find(motif_notes_grp_alter,full_song_notes_grp,selected_idx,verbose=verbose)
        total_selected_idx["vanilla"] = selected_idx
    
    return total_selected_idx



    selected_idx = []
    split_find(motif_notes_grp_alter,full_song_notes_grp,selected_idx,verbose=verbose)
    total_selected_idx["vanilla"] = selected_idx
    
    return total_selected_idx