
import pickle
import os
import glob
from miditoolkit.midi import parser as mid_parser
from miditoolkit.midi import containers as ct
import copy

import motif_labeling as motif_labeling

import argparse

parser = argparse.ArgumentParser(
    description="""Theme Extraction\nThis program extract polymophic themes from polymophic full compositions via altered LCS algorithm.\nThe extraction result is saved in pkl file and can also output to midi file for visulization.""")

parser.add_argument('--theme',help="theme midi file path",default="./sample_data/theme/MTD0827_Beethoven_Op007-01.mid")
parser.add_argument('--comp',help="full composition midi file path",default="./sample_data/full_composition/Beethoven_Op007-01.mid")
parser.add_argument('--result',help="theme extraction result file path (.pkl)")
parser.add_argument('--midi',help="theme extraction result midi file path")
parser.add_argument('-v', '--verbose',help="set verbose",action='store_true')


args = parser.parse_args()
# exit()


def proc_one(theme_file, comp_file, param_exps, verbose=False):
    midi_obj_theme = mid_parser.MidiFile(theme_file)

    midi_obj_fullcomp = mid_parser.MidiFile(comp_file)

    # merge all tracks
    comp_notes = []
    for ins in midi_obj_fullcomp.instruments:
        comp_notes.extend(ins.notes)
    motif_notes = []
    for ins in midi_obj_theme.instruments:
        motif_notes.extend(ins.notes)

    motif_notes.sort(key=lambda x: (x.start, x.pitch))
    comp_notes.sort(key=lambda x: (x.start, x.pitch))

    # # quantize fullsong
    # q_step = midi_obj_fullcomp.ticks_per_beat // 12
    # for n in comp_notes:
    #     n.start = int(q_step * round(n.start / q_step))
    #     n.end = int(q_step * round(n.end / q_step))

    # # quantize motif
    # q_step = midi_obj_theme.ticks_per_beat // 12
    # for n in motif_notes:
    #     n.start = int(q_step * round(n.start / q_step))
    #     n.end = int(q_step * round(n.end / q_step))

    motif_notes.sort(key=lambda x: (x.start, x.pitch))
    comp_notes.sort(key=lambda x: (x.start, x.pitch))

    # grouping notes
    comp_notes_grp = motif_labeling.group_ticks(comp_notes)
    motif_notes_grp = motif_labeling.group_ticks(motif_notes)

    zero_found = False
    all_exp_stats = {}
    for exp_name in param_exps:
        param = copy.deepcopy(param_exps[exp_name])
        param["distance_threshold"] = param["max_gap"]
        param["min_len"] = len(motif_notes) * param["min_len"]
        param["input_A_ticks_per_beat"] = midi_obj_theme.ticks_per_beat
        param["input_B_ticks_per_beat"] = midi_obj_fullcomp.ticks_per_beat

        ret = motif_labeling.motif_LCS(
            motif_notes_grp, comp_notes_grp, param=param, verbose=False)

        # calulate coverage
        coverage_stats = {}
        for t in ret:
            entry = {}
            idxs = ret[t]
            if verbose:
                print("Exp : {},  #matches: {}".format(exp_name, len(idxs)))
            entry["segment_count"] = len(idxs)
            entry["segment_group"] = []
            entry["segment_tick"] = []
            total_selected_g_idx = []

            idxs.sort(key=lambda x: (x[1][0]))

            for g in idxs:
                # g[0] : theme group idxs
                # g[1] : full comp group idxs
                ent_seg = [[g[0][0], g[0][-1]], [g[1][0], g[1][-1]]]
                ent_seg_tick = [[motif_notes_grp[g[0][0]]["start"], motif_notes_grp[g[0][-1]]["start"]], [
                    comp_notes_grp[g[1][0]]["start"], comp_notes_grp[g[1][-1]]["start"]]]
                entry["segment_group"].append(ent_seg)
                entry["segment_tick"].append(ent_seg_tick)

            if len(idxs) == 0:
                print("Zero found")
                zero_found = True
                entry["coverage"] = 0
                continue
            else:
                coverage = 0
                for x in entry["segment_tick"]:
                    coverage += x[1][1] - x[1][0]

                entry["coverage"] = coverage / midi_obj_fullcomp.max_tick
            coverage_stats[t] = entry
        if verbose:
            if 'vanilla' in coverage_stats:
                print("Coverage : {:.2f}".format(
                    coverage_stats['vanilla']['coverage']))
                all_exp_stats[exp_name] = coverage_stats['vanilla']
            else:
                print("Coverage : {:.2f}".format(
                    coverage_stats['pitch_shift']['coverage']))
                all_exp_stats[exp_name] = coverage_stats['pitch_shift']
            all_exp_stats[exp_name]["params"] = param_exps[exp_name]

    return all_exp_stats


# write the theme occurence into separate tracks
def output_midi(theme_file, comp_file, output_fn, coverage_result):
    midi_obj_theme = mid_parser.MidiFile(theme_file)
    theme_notes = midi_obj_theme.instruments[0].notes
    theme_notes.sort(key=lambda x: (x.start, x.pitch))
    theme_notes_grp = motif_labeling.group_ticks(theme_notes)

    midi_obj_comp = mid_parser.MidiFile(comp_file)

    comp_notes = []
    for ins in midi_obj_comp.instruments:
        comp_notes.extend(ins.notes)
    comp_notes.sort(key=lambda x: (x.start, x.pitch))
    comp_notes_grp = motif_labeling.group_ticks(comp_notes)

    new_mido_obj = mid_parser.MidiFile()
    new_mido_obj.ticks_per_beat = midi_obj_comp.ticks_per_beat
    new_mido_obj.tempo_changes = copy.deepcopy(midi_obj_comp.tempo_changes)

    new_track_fullsong = ct.Instrument(
        program=0, is_drum=False, name='full comp')
    new_track_fullsong.notes.extend(comp_notes)

    for i, grp in enumerate(coverage_result["segment_group"]):
        new_track_motif = ct.Instrument(
            program=0, is_drum=False, name='Theme Occur #{}'.format(i))
        for x in range(grp[1][0], grp[1][1]+1):
            new_track_motif.notes.extend(comp_notes_grp[x]["notes"])
        # new_track_motif.notes.extend(grp)
        new_mido_obj.instruments.append(new_track_motif)

    new_mido_obj.instruments.append(new_track_fullsong)
    new_mido_obj.dump(output_fn)


if __name__ == "__main__":
    # setup extraction hyperparameters
    param_exps = {
        "exp_default": {
            "max_gap": 0.7,
            "min_len": 0.4,
            "pitch_shift": False,
            "chroma": False,
            "reverse": False,
            "mirror": False
        }
    }

    # execute the extraction process
    result = proc_one(theme_file=args.theme,
                      comp_file=args.comp,
                      param_exps=param_exps,
                      verbose=args.v)
    # show the results
    print(result)
    if args.result:
        with open(args.result,'wb') as f:
            pickle.dump(result,f)

    if args.midi:
        # output the result to midi file
        output_midi(theme_file=args.theme,
                    comp_file=args.comp,
                    output_fn=args.midi,
                    coverage_result=result["exp_default"])
