import json, collections, sys
import numpy as np
COVS=("covered_1","covered_2_4","covered_5p"); FBS=("cur_unseen","prev_unseen","both_unseen")
def load(p):
    H=collections.defaultdict(int); N=collections.defaultdict(int)
    with open(p) as fh:
        hdr=json.loads(fh.readline())
        for line in fh:
            r=json.loads(line)
            k=(r["arm"],r["budget"],r["prompt_idx"],r["stratum"])
            H[k]+=r["hits"]; N[k]+=r["needed"]
    return hdr,H,N
for tag,p in (("P","results/real/prefetch_strat_s3.json.state.jsonl"),("R","results/real/prefetch_strat_s3_r.json.state.jsonl")):
    hdr,H,N=load(p)
    prompts=sorted({k[2] for k in N})
    def pool(arm,B,strata,excl=None):
        h=sum(H[(arm,B,q,s)] for q in prompts for s in strata if q!=excl)
        n=sum(N[(arm,B,q,s)] for q in prompts for s in strata if q!=excl)
        return h,n
    def d(a,b,strata,excl=None,B=16):
        ha,n=pool(a,B,strata,excl); hb,nb=pool(b,B,strata,excl); assert n==nb
        return (ha-hb)/n
    # prompt-13 share of both-unseen positions
    nb={q:N[("history_tok",16,q,"both_unseen")] for q in prompts}
    tot=sum(nb.values()); top=max(nb,key=nb.get)
    print(tag,"both_unseen top prompt",top,round(nb[top]/tot,4),"prompts with >0:",sum(1 for v in nb.values() if v>0))
    print(tag,"D_eq both_unseen w/o 13",round(d("history_tok","free_bigram_b",("both_unseen",),13),4),
          "D_eq^FB w/o 13",round(d("history_tok","free_bigram_b",FBS,13),4))
    covs=[d("history_tok","free_bigram_b",COVS,q) for q in prompts]
    pts=[d("history_tok_pt","free_bigram_pt",COVS+FBS,q) for q in prompts]
    print(tag,"max D_eq^COV LOO",round(max(covs),4),"min D_eq^PT LOO",round(min(pts),4))
    # decomposition identity at B=16
    full=d("history_tok","free_bigram_b",COVS+FBS); c=d("history_tok","free_bigram_b",COVS); f=d("history_tok","free_bigram_b",FBS)
    sc=pool("history_tok",16,COVS)[1]/pool("history_tok",16,COVS+FBS)[1]
    print(tag,"decomp |diff|",abs(full-(sc*c+(1-sc)*f)))
    # B=32 twin-style comparison: D_eq vs D_eq^PT at B=32 on all
    print(tag,"B32 D_eq",round(d("history_tok","free_bigram_b",COVS+FBS,B=32),4),"D_eq^PT",round(d("history_tok_pt","free_bigram_pt",COVS+FBS,B=32),4),
          "PT gain B32",round(d("free_bigram_pt","free_bigram_b",COVS+FBS,B=32),4))
    # sparse covered D_eq union (1-4)
    print(tag,"D_eq covered_1+2_4 pooled",round(d("history_tok","free_bigram_b",("covered_1","covered_2_4")),4))
