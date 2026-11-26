# Wild roe deer POH: matched recorded-road-distance sensitivity, nonchronological.
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
  x <- read.csv(file.path(root,"data_spaceuse_roedeer.csv"),stringsAsFactors=FALSE)
  stopifnot(identical(names(x),c("ANIMAL","AGE","SEX","MONTH","YEAR","POH","dist_road")),
            nrow(x)==2288,length(unique(x$ANIMAL))==256)
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
    is.finite(x$MONTH)&x$MONTH%in%1:12&is.finite(x$POH)&x$POH>=0&x$POH<=1
  y<-x[valid,]
  # A recorded YEAR+MONTH key is not asserted to be an observation date.
  y$PERIOD<-sprintf("%04d-%02d",y$YEAR,y$MONTH)
  groups<-split(seq_len(nrow(y)),paste(y$ANIMAL,y$PERIOD,sep="|"))
  keep<-vapply(groups,function(ix)length(unique(y$AGE[ix]))==1&&length(unique(y$SEX[ix]))==1,logical(1))
  stopifnot(all(keep))  # no silent choice of metadata for duplicate cells
  cells<-lapply(groups,function(ix){z<-y[ix[1],];z$POH<-mean(y$POH[ix]);z})
  t<-do.call(rbind,cells);rownames(t)<-NULL
  t<-t[order(t$ANIMAL,t$YEAR,t$MONTH),]
  idsex<-split(t$SEX,t$ANIMAL);stopifnot(all(vapply(idsex,function(z)length(unique(z))==1,logical(1))))
  list(t=t,G=G,qa=list(raw_rows=nrow(x),raw_horses=length(unique(x$ANIMAL)),
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
prepare <- function(t,G,seed,road=FALSE) {
  ids<-sort(unique(t$ANIMAL));set.seed(seed)
  # Two disjoint donor/focal halves, all animals evaluated once if eligible.
  half<-setNames(sample(rep(0:1,length.out=length(ids))),ids)
  X<-design(t)
  panels<-list()
  for(h in 0:1) {
    di<-which(half[t$ANIMAL]!=h);fi<-which(half[t$ANIMAL]==h)
    td<-t[di,]
    w<-1/as.numeric(table(td$ANIMAL)[td$ANIMAL])
    Xh<-X
    if(road){
      stopifnot(all(is.finite(t$dist_road)),all(t$dist_road>=0))
      mu<-sum(w*td$dist_road)/sum(w)
      sd<-sqrt(sum(w*(td$dist_road-mu)^2)/sum(w))
      if(!is.finite(sd)||sd<=0)stop('HOLD_ROAD_VARIATION')
      Xh<-cbind(X,road=(t$dist_road-mu)/sd)
    }
    xd<-Xh[di,,drop=FALSE]
    pen<-diag(ncol(Xh));pen[1,1]<-0
    beta<-solve(crossprod(xd,xd*w)+pen,crossprod(xd,w*td$POH))
    pred<-as.numeric(Xh%*%beta)
    dr<-tapply(td$POH-pred[di],td$ANIMAL,mean)
    donor<-names(dr)
    targets<-list()
    for(id in sort(unique(t$ANIMAL[fi]))) {
      ix<-which(t$ANIMAL==id)
      if(length(ix)<max(DEPTHS)+1)next
      # Same target across all depths. Draw without reference to POH.
      chosen<-sample(ix,length(ix),replace=FALSE)
      target<-chosen[1];other<-chosen[-1]
      stopifnot(!(target%in%other),all(t$ANIMAL[other]==id),!(id%in%donor))
      b<-vapply(DEPTHS,function(n)pred[target]+(
          if(n==0)0 else sum(t$POH[other[seq_len(n)]]-pred[other[seq_len(n)]])/(n+SHRINK)),numeric(1))
      targets[[length(targets)+1L]]<-list(id=id,y=t$POH[target],b=b,mask=c(target,other[seq_len(max(DEPTHS))]))
    }
    if(!length(targets))stop("HOLD_EMPTY_FOCAL_HALF")
    panels[[h+1]]<-list(ids=vapply(targets,function(q)q$id,character(1)),
       y=vapply(targets,function(q)q$y,numeric(1)),B=do.call(rbind,lapply(targets,function(q)q$b)),
       donors=donor,dr=as.numeric(dr),mask=do.call(rbind,lapply(targets,function(q)q$mask)))
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
       gain=colMeans(g),change=mean(g[,3]-g[,1]),alignment=mean(d*u),
       clipped_gain=colMeans((Y-pmin(1,pmax(0,B)))^2-(Y-pmin(1,pmax(0,F)))^2))
}
run_seed <- function(t,G,seed,road=FALSE) {
  p<-prepare(t,G,seed,road)
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
  summary<-list(status="OBSERVED_MASKED_DEPTH",n=n,
       donors_per_fold=vapply(p,function(q)length(q$donors),integer(1)),
       targets_per_fold=vapply(p,function(q)length(q$ids),integer(1)),
       depth=DEPTHS,N_RMSE=z$N,F_RMSE=z$F,full_gain=z$gain,change_3_minus_0=z$change,
       mean_du=z$alignment,clipped_gain=z$clipped_gain,
       fixed_prediction_deer_bootstrap_97_5=unname(intervals),
       permuted_label_summary=list(draws=PERMS,quantiles=unname(apply(null,2,quantile,c(.025,.5,.975))),
          columns=c("gain_0","change_3_minus_0","mean_du"),
          gain_0_exceeds_count=sum(z$gain[1]>null[,1]),
          more_negative_change_count=sum(z$change<null[,2]),
          descriptive_plus_one_tail_gain=(1+sum(null[,1]>=z$gain[1]))/(PERMS+1),
          descriptive_plus_one_tail_change=(1+sum(null[,2]<=z$change))/(PERMS+1)),
       qualification="Retrospective, artificial record revelation, not chronological forecasts; bootstrap conditional, permutation exchangeability not established.")
  list(summary=summary,p=p,z=z)
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

# Compare two fitted corrections on exactly the same held-out records.
paired <- function(a,b,seed){
  stopifnot(length(a$p)==length(b$p),all(vapply(seq_along(a$p),function(i){
    x<-a$p[[i]];y<-b$p[[i]]
    identical(x$ids,y$ids)&&identical(x$donors,y$donors)&&identical(x$mask,y$mask)&&identical(x$y,y$y)
  },logical(1))))
  ga<-a$z$g;gb<-b$z$g;n<-nrow(ga)
  delta<-cbind(gb[,1]-ga[,1],(gb[,3]-gb[,1])-(ga[,3]-ga[,1]))
  set.seed(seed+3L)
  ix<-matrix(sample.int(n,n*BOOT,replace=TRUE),nrow=BOOT)
  ci<-t(vapply(1:2,function(j)quantile(rowMeans(matrix(delta[,j][ix],nrow=BOOT)),c(.0125,.9875),names=FALSE),numeric(2)))
  list(columns=c("gain0_road_minus_base","change_road_minus_base"),mean=colMeans(delta),conditional_97_5=unname(ci),
       base_own_rmse_change=b$z$N-a$z$N,genome_rmse_change=b$z$F-a$z$F)
}
args<-commandArgs(trailingOnly=TRUE)
if(identical(args,"--self-test")){
  self_test()
  # Road enters the design without changing masks in this invented cohort.
  t<-expand.grid(ANIMAL=paste0("d",1:12),MONTH=1:4,stringsAsFactors=FALSE)
  t$AGE<-rep(c("adult","young"),length.out=nrow(t));t$SEX<-rep(c("f","f","m","m"),length.out=nrow(t))
  t$YEAR<-2020;t$dist_road<-seq_len(nrow(t));t$POH<-(t$dist_road%%11)/11
  G<-diag(12);rownames(G)<-colnames(G)<-paste0("d",1:12)
  a<-prepare(t,G,20261124L,FALSE);b<-prepare(t,G,20261124L,TRUE)
  stopifnot(all(vapply(1:2,function(i)identical(a[[i]]$mask,b[[i]]$mask),logical(1))))
  stopifnot(any(abs(a[[1]]$B-b[[1]]$B)>1e-8))
  cat("Road design and mask parity synthetic checks passed\n");quit(save="no",status=0)
}
stopifnot(length(args)==3)
d<-load_panel(args[1]);old<-read_json(args[3],simplifyVector=TRUE)$result
stopifnot(d$qa$duplicate_rows_collapsed==0)
# No missing road record is silently imputed. Match complete records in both arms.
valid_road<-is.finite(d$t$dist_road)&d$t$dist_road>=0
t<-d$t[valid_road,]
road_by_deer<-split(t$dist_road,t$ANIMAL)
qa<-c(d$qa,list(road_valid_rows=nrow(t),road_invalid_rows=sum(!valid_road),road_deer=length(road_by_deer),
    road_deer_constant=sum(vapply(road_by_deer,function(x)length(unique(x))==1,logical(1))),
    road_ge4=sum(table(t$ANIMAL)>=4)))
stopifnot(qa$road_ge4>=MIN_TARGET)
res<-setNames(lapply(SEEDS,function(seed){
  a<-run_seed(d$t,d$G,seed,FALSE)
  reference<-old$results[[as.character(seed)]]
  stopifnot(max(abs(a$summary$full_gain-reference$full_gain))<1e-10,
            max(abs(a$summary$N_RMSE-reference$N_RMSE))<1e-10,
            max(abs(a$summary$F_RMSE-reference$F_RMSE))<1e-10)
  if(!all(valid_road))a<-run_seed(t,d$G,seed,FALSE)
  b<-run_seed(t,d$G,seed,TRUE)
  list(base=a$summary,road=b$summary,paired=paired(a,b,seed),original_gain_parity=TRUE)
}),as.character(SEEDS))
out<-list(status="RETROSPECTIVE_POH_ROAD_CONTEXT_SENSITIVITY",primary_seed=SEEDS[1],qa=qa,
    source="Dryad 10.5061/dryad.dbrv15dxg v1 locked file content",
    results=res,limitations=c("Recorded road distance can be a contemporaneous or outcome-associated variable; not a causal or future-known environmental covariate.",
    "Same-source, post-POH-result sensitivity; no independent replication. Conditional deer bootstrap excludes shared kin/spatial/donor fit dependence.",
    "No claim that road distance exhausts shared spatial environment. No raw values, masks or IDs exported."))
write_json(out,args[2],pretty=TRUE,auto_unbox=TRUE,digits=16)
cat(toJSON(out,auto_unbox=TRUE,digits=16),"\n")
