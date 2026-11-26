# Wild roe deer: SPEED endpoint, nonchronological masked-observation information-depth test.
# Parallel endpoint adaptation of the frozen POH script; do not clip recorded SPEED.
# No prediction of future dates or genetic causation. No animal IDs exported.
suppressPackageStartupMessages(library(jsonlite))
SEEDS <- c(20261124L,20261125L,20261126L)
DEPTHS <- c(0L,1L,3L)
MIN_TARGET <- 100L
PERMS <- 199L
BOOT <- 999L
LAMBDA <- 1
SHRINK <- 3

load_panel <- function(root) {
  x <- read.csv(file.path(root,"data_movement_roedeer.csv"),stringsAsFactors=FALSE)
  stopifnot(identical(names(x),c("ANIMAL","AGE","SEX","MONTH","YEAR","SPEED")),
            nrow(x)==1856,length(unique(x$ANIMAL))==205)
  env<-new.env(parent=emptyenv()); n<-load(file.path(root,"grm_readytouse.Rdata"),envir=env)
  stopifnot("b"%in%n)
  G<-as.matrix(get("b",envir=env,inherits=FALSE))
  stopifnot(is.numeric(G),identical(dim(G),c(334L,334L)),all(is.finite(G)),
            !is.null(rownames(G)),identical(rownames(G),colnames(G)),
            !anyDuplicated(rownames(G)),max(abs(G-t(G)))<1e-10,
            all(x$ANIMAL%in%rownames(G)))
  eig<-eigen(G,symmetric=TRUE,only.values=TRUE)$values
  stopifnot(min(eig)+LAMBDA>1e-8)
  valid<-!is.na(x$ANIMAL)&nzchar(x$ANIMAL)&!is.na(x$AGE)&nzchar(x$AGE)&
    !is.na(x$SEX)&nzchar(x$SEX)&is.finite(x$YEAR)&x$YEAR>=1900&x$YEAR<=2100&
    is.finite(x$MONTH)&x$MONTH%in%1:12&is.finite(x$SPEED)
  y<-x[valid,]
  # A recorded YEAR+MONTH key is not asserted to be an observation date.
  y$PERIOD<-sprintf("%04d-%02d",y$YEAR,y$MONTH)
  groups<-split(seq_len(nrow(y)),paste(y$ANIMAL,y$PERIOD,sep="|"))
  keep<-vapply(groups,function(ix)length(unique(y$AGE[ix]))==1&&length(unique(y$SEX[ix]))==1,logical(1))
  stopifnot(all(keep))  # no silent choice of metadata for duplicate cells
  cells<-lapply(groups,function(ix){z<-y[ix[1],];z$SPEED<-mean(y$SPEED[ix]);z})
  t<-do.call(rbind,cells);rownames(t)<-NULL
  t<-t[order(t$ANIMAL,t$YEAR,t$MONTH),]
  idsex<-split(t$SEX,t$ANIMAL);stopifnot(all(vapply(idsex,function(z)length(unique(z))==1,logical(1))))
  list(t=t,G=G,qa=list(raw_rows=nrow(x),raw_deer=length(unique(x$ANIMAL)),
       valid_rows=nrow(y),distinct_cells=nrow(t),duplicate_rows_collapsed=nrow(y)-nrow(t),
       animals=length(unique(t$ANIMAL)),eligible_ge4=sum(table(t$ANIMAL)>=4),
       grm_n=nrow(G),grm_min_eigenvalue=min(eig),grm_max_eigenvalue=max(eig),
       ridge=LAMBDA,minimum_shifted_eigenvalue=min(eig)+LAMBDA))
}
design <- function(t) {
  # Fixed outcome-blind columns. No date interpretation or full-period
  # environmental similarities; donor-fitted sex/age/month mean structure.
  mm<-model.matrix(~factor(MONTH,levels=1:12)*factor(SEX)+factor(AGE),data=t)
  if(any(!is.finite(mm)))stop("HOLD_DESIGN")
  mm
}
gain <- function(y,b,d) mean((y-b)^2-(y-b-d)^2)
safe_solve <- function(K,residual) {
  z<-K+diag(LAMBDA,nrow(K))
  if(!isSymmetric(z,tol=1e-10))stop("HOLD_KERNEL_SYMMETRY")
  R<-chol(z)
  backsolve(R,forwardsolve(t(R),residual))
}
prepare <- function(t,G,seed) {
  ids<-sort(unique(t$ANIMAL));set.seed(seed)
  # Two disjoint donor/focal halves, all animals evaluated once if eligible.
  half<-setNames(sample(rep(0:1,length.out=length(ids))),ids)
  X<-design(t)
  panels<-list()
  for(h in 0:1) {
    di<-which(half[t$ANIMAL]!=h);fi<-which(half[t$ANIMAL]==h)
    td<-t[di,]; xd<-X[di,,drop=FALSE]
    w<-1/as.numeric(table(td$ANIMAL)[td$ANIMAL])
    pen<-diag(ncol(X));pen[1,1]<-0
    beta<-solve(crossprod(xd,xd*w)+pen,crossprod(xd,w*td$SPEED))
    pred<-as.numeric(X%*%beta)
    dr<-tapply(td$SPEED-pred[di],td$ANIMAL,mean)
    donor<-names(dr)
    targets<-list()
    for(id in sort(unique(t$ANIMAL[fi]))) {
      ix<-which(t$ANIMAL==id)
      if(length(ix)<max(DEPTHS)+1)next
      # Same target across all depths. Draw without reference to SPEED.
      chosen<-sample(ix,length(ix),replace=FALSE)
      target<-chosen[1];other<-chosen[-1]
      stopifnot(!(target%in%other),all(t$ANIMAL[other]==id),!(id%in%donor))
      b<-vapply(DEPTHS,function(n)pred[target]+(
          if(n==0)0 else sum(t$SPEED[other[seq_len(n)]]-pred[other[seq_len(n)]])/(n+SHRINK)),numeric(1))
      targets[[length(targets)+1L]]<-list(id=id,y=t$SPEED[target],b=b)
    }
    if(!length(targets))stop("HOLD_EMPTY_FOCAL_HALF")
    panels[[h+1]]<-list(ids=vapply(targets,function(q)q$id,character(1)),
       y=vapply(targets,function(q)q$y,numeric(1)),B=do.call(rbind,lapply(targets,function(q)q$b)),
       donors=donor,dr=as.numeric(dr))
  }
  stopifnot(!anyDuplicated(unlist(lapply(panels,function(p)p$ids))),all(vapply(panels,function(p)!any(p$ids%in%p$donors),logical(1))))
  panels
}
correction <- function(p,G,map) {
  d<-unname(map[p$donors]);f<-unname(map[p$ids])
  alpha<-safe_solve(G[d,d,drop=FALSE],p$dr)
  as.numeric(G[f,d,drop=FALSE]%*%alpha)
}
score <- function(panels,G,map) {
  ys<-unlist(lapply(panels,function(p)p$y))
  B<-do.call(rbind,lapply(panels,function(p)p$B))
  d<-unlist(lapply(panels,function(p)correction(p,G,map)))
  Y<-matrix(ys,nrow=nrow(B),ncol=ncol(B))
  F<-B+d
  g<-(Y-B)^2-(Y-F)^2
  u<-B[,3]-B[,1]
  stopifnot(max(abs(g[,3]-g[,1]+2*d*u))<1e-10)
  list(g=g,d=d,u=u,N=sqrt(colMeans((Y-B)^2)),F=sqrt(colMeans((Y-F)^2)),
       gain=colMeans(g),change=mean(g[,3]-g[,1]),alignment=mean(d*u))
}
run_seed <- function(t,G,seed) {
  p<-prepare(t,G,seed)
  n<-sum(vapply(p,function(z)length(z$ids),integer(1)))
  if(n<MIN_TARGET)return(list(status="HOLD_TARGET_SUPPORT",n=n))
  ids<-sort(unique(t$ANIMAL));base<-setNames(ids,ids)
  z<-score(p,G,base)
  set.seed(seed+1L)
  # Shuffle genomic labels within recorded sex; preserve matrix geometry
  # and all observation masks, baseline/donor responses, and fold assignment.
  sex<-vapply(split(t$SEX,t$ANIMAL),function(v)v[1],character(1))
  blocks<-split(ids,sex[ids])
  null<-matrix(NA_real_,nrow=PERMS,ncol=3)
  for(i in seq_len(PERMS)) {
    map<-base
    for(b in blocks)map[b]<-sample(b,length(b),replace=FALSE)
    q<-score(p,G,map)
    null[i,]<-c(q$gain[1],q$change,q$alignment)
  }
  set.seed(seed+2L)
  ix<-matrix(sample.int(n,n*BOOT,replace=TRUE),nrow=BOOT)
  b0<-rowMeans(matrix(z$g[,1][ix],nrow=BOOT))
  # Explicit vector indexing into original per-animal gain differences.
  delta<-z$g[,3]-z$g[,1]
  bd<-rowMeans(matrix(delta[ix],nrow=BOOT))
  # Conditional deer bootstrap, not full pedigree/spatial dependence or fit uncertainty.
  intervals<-rbind(quantile(b0,c(.0125,.9875),names=FALSE),quantile(bd,c(.0125,.9875),names=FALSE))
  list(status="OBSERVED_MASKED_DEPTH",n=n,
       donors_per_fold=vapply(p,function(q)length(q$donors),integer(1)),
       targets_per_fold=vapply(p,function(q)length(q$ids),integer(1)),
       depth=DEPTHS,N_RMSE=z$N,F_RMSE=z$F,full_gain=z$gain,change_3_minus_0=z$change,
       mean_du=z$alignment,
       fixed_prediction_deer_bootstrap_97_5=unname(intervals),
       permuted_label_summary=list(draws=PERMS,quantiles=unname(apply(null,2,quantile,c(.025,.5,.975))),
          columns=c("gain_0","change_3_minus_0","mean_du"),
          gain_0_exceeds_count=sum(z$gain[1]>null[,1]),
          more_negative_change_count=sum(z$change<null[,2]),
          descriptive_plus_one_tail_gain=(1+sum(null[,1]>=z$gain[1]))/(PERMS+1),
          descriptive_plus_one_tail_change=(1+sum(null[,2]<=z$change))/(PERMS+1)),
       qualification="Retrospective, artificial record revelation, not chronological forecasts; bootstrap conditional, permutation exchangeability not established.")
}
self_test <- function() {
  G<-diag(12);rownames(G)<-colnames(G)<-paste0("x",1:12)
  p<-list(list(ids=c("x1","x2"),donors=c("x3","x4"),dr=c(.1,.2),y=c(.2,.8),
       B=matrix(c(.4,.4,.5,.5,.6,.7),nrow=2)))
  map<-setNames(rownames(G),rownames(G))
  z<-score(p,G,map);stopifnot(all(abs(z$gain)<1e-12))
  G["x1","x3"]<-G["x3","x1"]<-.4
  z<-score(p,G,map)
  stopifnot(abs(z$d[1]-.02)<1e-12,abs(z$change+2*z$alignment)<1e-12)
  # Reject an indefinite shifted training block.
  bad<-matrix(c(1,3,3,1),2)
  ok<-tryCatch({safe_solve(bad,c(1,1));FALSE},error=function(e)TRUE)
  stopifnot(ok)
  cat("Synthetic fixed-correction and regularization tests passed\n")
}
args<-commandArgs(trailingOnly=TRUE)
if(identical(args,"--self-test")){self_test();quit(save="no",status=0)}
stopifnot(length(args)==2)
d<-load_panel(args[1]);z<-setNames(lapply(SEEDS,function(s)run_seed(d$t,d$G,s)),as.character(SEEDS))
res<-list(status="RETROSPECTIVE_ROE_DEER_SPEED_MASKED_OBSERVATION_DEPTH",primary_seed=SEEDS[1],
  source="Dryad 10.5061/dryad.dbrv15dxg v1, locked content",qa=d$qa,results=z,
  limitations=c("Not a chronological forecast; YEAR+MONTH only defines recorded candidate periods.",
    "Different target masks and folds share the same source animals.",
    "Genomic labels are not causal inheritance and may track space or management.",
    "Regularized signed matrix prediction; no heritability estimated.",
    "No individual IDs, records, GRM values or predictions exported."))
write_json(res,args[2],pretty=TRUE,auto_unbox=TRUE,digits=16)
cat(toJSON(res,auto_unbox=TRUE,digits=16),"\n")
