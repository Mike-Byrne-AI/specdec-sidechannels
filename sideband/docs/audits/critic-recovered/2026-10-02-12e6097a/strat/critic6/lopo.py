import json, numpy as np
R="C:/Users/<user>/Desktop/Research/sideband/results/real/"
STR=["covered_1","covered_2_4","covered_5p","cur_unseen","prev_unseen","both_unseen"]
U={"covered":STR[:3],"fallback":STR[3:],"all":STR}
for h in ["","_r"]:
    H={}; N={}
    with open(R+"prefetch_strat_s3%s.json.state.jsonl"%h,encoding="utf-8") as f:
        f.readline()
        for l in f:
            r=json.loads(l)
            if r["budget"]!=16: continue
            k=(r["arm"],r["prompt_idx"],r["stratum"])
            H[k]=H.get(k,0)+r["hits"]; N[k]=N.get(k,0)+r["needed"]
    prompts=sorted(set(k[1] for k in H))
    def rate(arm,strata,excl=None):
        h=sum(H.get((arm,p,s),0) for p in prompts if p!=excl for s in strata)
        n=sum(N.get((arm,p,s),0) for p in prompts if p!=excl for s in strata)
        return h/n
    def de(a,b,strata,excl=None): return rate(a,strata,excl)-rate(b,strata,excl)
    # prompt 13 share of both_unseen positions (needed via history_tok, summed over gates -> /16/8)
    tot=sum(N[("history_tok",p,"both_unseen")] for p in prompts if ("history_tok",p,"both_unseen") in N)
    print(h or "_p","n prompts",len(prompts),"p13 share of both_unseen %.4f"%(N.get(("history_tok",13,"both_unseen"),0)/tot), "prompts w/ both_unseen", sum(1 for p in prompts if N.get(("history_tok",p,"both_unseen"),0)>0))
    print("  full: both %.4f FB %.4f COV %.4f EQPT %.4f"%(de("history_tok","free_bigram_b",["both_unseen"]),de("history_tok","free_bigram_b",U["fallback"]),de("history_tok","free_bigram_b",U["covered"]),de("history_tok_pt","free_bigram_pt",U["all"])))
    print("  drop13: both %.4f FB %.4f"%(de("history_tok","free_bigram_b",["both_unseen"],13),de("history_tok","free_bigram_b",U["fallback"],13)))
    covs=[de("history_tok","free_bigram_b",U["covered"],p) for p in prompts]
    eqpt=[de("history_tok_pt","free_bigram_pt",U["all"],p) for p in prompts]
    print("  LOPO max COV %.4f (drop %d); min EQPT %.4f (drop %d)"%(max(covs),prompts[int(np.argmax(covs))],min(eqpt),prompts[int(np.argmin(eqpt))]))
