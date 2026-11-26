# Same-deer, same-period POH/SPEED comparison, not chronological.
# No prediction of future dates or genetic causation. No animal IDs exported.
suppressPackageStartupMessages(library(jsonlite))
SEEDS <- c(20261124L,20261125L,20261126L)
DEPTHS <- c(0L,1L,3L)
MIN_TARGET <- 100L
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

match_panel <- function(root){
  d<-load_panel(root)
  a<-d$t
  b<-read.csv(file.path(root,"data_movement_roedeer.csv"),stringsAsFactors=FALSE)
  stopifnot(identical(names(b),c("ANIMAL","AGE","SEX","MONTH","YEAR","SPEED")),
            nrow(b)==1856,length(unique(b$ANIMAL))==205,all(b$ANIMAL%in%rownames(d$G)))
  ok<-!is.na(b$ANIMAL)&nzchar(b$ANIMAL)&!is.na(b$AGE)&nzchar(b$AGE)&
    !is.na(b$SEX)&nzchar(b$SEX)&is.finite(b$YEAR)&b$YEAR>=1900&b$YEAR<=2100&
    is.finite(b$MONTH)&b$MONTH%in%1:12&is.finite(b$SPEED)
  b<-b[ok,];b$PERIOD<-sprintf("%04d-%02d",b$YEAR,b$MONTH)
  gr<-split(seq_len(nrow(b)),paste(b$ANIMAL,b$PERIOD,sep="|"))
  stopifnot(all(vapply(gr,function(i)length(unique(b$AGE[i]))==1&&length(unique(b$SEX[i]))==1,logical(1))))
  b2<-do.call(rbind,lapply(gr,function(i){z<-b[i[1],];z$SPEED<-mean(b$SPEED[i]);z}))
  j<-merge(a,b2[,c("ANIMAL","PERIOD","AGE","SEX","SPEED")],by=c("ANIMAL","PERIOD"),suffixes=c(".p",".s"))
  same<-j$AGE.p==j$AGE.s&j$SEX.p==j$SEX.s
  stopifnot(!anyNA(same))
  x<-j[same,];x$AGE<-x$AGE.p;x$SEX<-x$SEX.p
  count<-table(x$ANIMAL);keep<-names(count[count>=4])
  t<-x[x$ANIMAL%in%keep,];t<-t[order(t$ANIMAL,t$PERIOD),]
  stopifnot(!anyDuplicated(paste(t$ANIMAL,t$PERIOD)),all(vapply(split(t$SEX,t$ANIMAL),function(v)length(unique(v))==1,logical(1))))
  list(t=t,G=d$G,qa=list(poh_cells=nrow(a),speed_valid_rows=nrow(b),speed_cells=nrow(b2),speed_duplicates=nrow(b)-nrow(b2),
     shared_deer_before_period_match=length(intersect(unique(a$ANIMAL),unique(b2$ANIMAL))),
     joined_cells=nrow(j),metadata_disagreements=sum(!same),concordant_cells=nrow(x),
     concordant_deer=length(count),eligible_deer=length(keep),eligible_cells=nrow(t)))
}
# Equal-deer-weighted residual moment estimand. Each individual contributes
# average residual, average squared residual and ordered distinct-pair product.
mom <- function(r){
  n<-length(r);stopifnot(n>=2,all(is.finite(r)))
  c(m=mean(r),q=mean(r^2),p=(sum(r)^2-sum(r^2))/(n*(n-1)))
}
repstat <- function(M){
  v<-colMeans(M);den<-v[2]-v[1]^2
  if(!is.finite(den)||den<=1e-12)return(NA_real_)
  (v[3]-v[1]^2)/den
}
summarize_trait <- function(z,M) {
  G<-as.matrix(z[,c("g0","g1","g3")])
  list(n=nrow(z),gain=colMeans(G),change=mean(G[,3]-G[,1]),
       repeatability=repstat(M),rmse_no_genome=sqrt(colMeans(as.matrix(z[,c("n0","n1","n3")]))),
       rmse_genome=sqrt(colMeans(as.matrix(z[,c("f0","f1","f3")]))))
}
one_seed<-function(t,G,seed){
  ids<-sort(unique(t$ANIMAL));set.seed(seed)
  half<-setNames(sample(rep(0:1,length.out=length(ids))),ids)
  X<-design(t);Y<-as.matrix(t[,c("POH","SPEED")])
  rows<-list();moms<-list()
  for(h in 0:1){
    di<-which(half[t$ANIMAL]!=h);fi<-which(half[t$ANIMAL]==h)
    td<-t[di,];w<-1/as.numeric(table(td$ANIMAL)[td$ANIMAL])
    mu<-colSums(Y[di,,drop=FALSE]*w)/sum(w)
    sc<-sqrt(colSums(sweep(Y[di,,drop=FALSE],2,mu)^2*w)/sum(w))
    stopifnot(all(is.finite(sc)),all(sc>1e-10))
    Z<-sweep(sweep(Y,2,mu),2,sc,"/")
    xd<-X[di,,drop=FALSE];pen<-diag(ncol(X));pen[1,1]<-0
    beta<-solve(crossprod(xd,xd*w)+pen,crossprod(xd,Z[di,,drop=FALSE]*w))
    pred<-X%*%beta;R<-Z-pred
    donors<-sort(unique(td$ANIMAL))
    dr<-do.call(rbind,lapply(donors,function(id)colMeans(R[di[td$ANIMAL==id],,drop=FALSE])))
    rownames(dr)<-donors
    K<-G[donors,donors,drop=FALSE]+diag(LAMBDA,length(donors))
    ch<-chol(K);alpha<-backsolve(ch,forwardsolve(t(ch),dr))
    focal<-sort(unique(t$ANIMAL[fi]))
    stopifnot(!any(focal%in%donors))
    gd<-G[focal,donors,drop=FALSE]%*%alpha
    for(i in seq_along(focal)){
      id<-focal[i];ix<-which(t$ANIMAL==id);stopifnot(length(ix)>=4)
      chosen<-sample(ix,length(ix),replace=FALSE);target<-chosen[1];other<-chosen[-1]
      stopifnot(!(target%in%other))
      for(k in 1:2){
        B<-vapply(DEPTHS,function(n)pred[target,k]+if(n==0)0 else sum(R[other[seq_len(n)],k])/(n+SHRINK),numeric(1))
        dd<-gd[i,k];err<-Z[target,k]-B;g<-err^2-(err-dd)^2
        stopifnot(abs((g[3]-g[1])+2*dd*(B[3]-B[1]))<1e-10)
        rows[[length(rows)+1L]]<-data.frame(id=id,trait=k,g0=g[1],g1=g[2],g3=g[3],n0=err[1]^2,n1=err[2]^2,n3=err[3]^2,
          f0=(err[1]-dd)^2,f1=(err[2]-dd)^2,f3=(err[3]-dd)^2)
        moms[[length(moms)+1L]]<-mom(R[ix,k])
      }
    }
  }
  z<-do.call(rbind,rows);M<-do.call(rbind,moms)
  p<-z$trait==1;s<-z$trait==2
  stopifnot(identical(z$id[p],z$id[s]),!anyDuplicated(z$id[p]),sum(p)==length(ids))
  a<-z[p,];b<-z[s,];A<-M[p,,drop=FALSE];B<-M[s,,drop=FALSE]
  aa<-summarize_trait(a,A);bb<-summarize_trait(b,B)
  contrast<-function(ix)c(repeatability=repstat(A[ix,,drop=FALSE])-repstat(B[ix,,drop=FALSE]),
     initial_gain=mean(a$g0[ix]-b$g0[ix]),
     depth_change=mean((a$g3[ix]-a$g0[ix])-(b$g3[ix]-b$g0[ix])))
  set.seed(seed+7L)
  bt<-replicate(BOOT,contrast(sample.int(nrow(a),nrow(a),replace=TRUE)))
  if(any(!is.finite(bt)))stop("HOLD_BOOTSTRAP_VARIANCE")
  ci<-t(apply(bt,1,quantile,c(0.05/6,1-0.05/6),names=FALSE))
  list(status="OBSERVED_MATCHED_TRAITS",POH=aa,SPEED=bb,contrast_names=c("POH_minus_SPEED_repeatability","POH_minus_SPEED_initial_standardized_gain","POH_minus_SPEED_depth_change"),
    contrasts=unname(contrast(seq_len(nrow(a)))),conditional_98_333_intervals=unname(ci))
}
self_test<-function(){
  stopifnot(max(abs(mom(c(1,2,3))-c(2,14/3,11/3)))<1e-12)
  x<-rbind(mom(c(-1,-1,-1)),mom(c(1,1,1)))
  stopifnot(abs(repstat(x)-1)<1e-12)
  x<-rbind(mom(c(-1,1)),mom(c(-1,1)));stopifnot(abs(repstat(x)+1)<1e-12)
  # Identical traits give zero paired contrast on an invented matched cohort.
  t<-expand.grid(ANIMAL=paste0("d",1:12),MONTH=1:4,stringsAsFactors=FALSE)
  t$AGE<-rep(c("adult","young"),length.out=nrow(t));t$SEX<-rep(c("f","f","m","m"),length.out=nrow(t))
  t$YEAR<-2020;t$POH<-(seq_len(nrow(t))%%11)/11;t$SPEED<-t$POH
  G<-diag(12);rownames(G)<-colnames(G)<-paste0("d",1:12)
  G["d1","d2"]<-G["d2","d1"]<-.2
  z<-one_seed(t,G,20261124L)
  stopifnot(max(abs(z$contrasts))<1e-12,max(abs(z$conditional_98_333_intervals))<1e-12)
  cat("Matched trait and repeatability synthetic tests passed\n")
}
args<-commandArgs(trailingOnly=TRUE)
if(identical(args,"--self-test")){self_test();quit(save="no",status=0)}
stopifnot(length(args)==2)
d<-match_panel(args[1])
out<-list(status=if(d$qa$eligible_deer<MIN_TARGET)"HOLD_MATCHED_SUPPORT" else "RETROSPECTIVE_MATCHED_TRAIT_REPEATABILITY",
  primary_seed=SEEDS[1],qa=d$qa,
  results=if(d$qa$eligible_deer<MIN_TARGET)NULL else setNames(lapply(SEEDS,function(seed)one_seed(d$t,d$G,seed)),as.character(SEEDS)),
  limitations=c("Exact recorded period labels are not established chronological observations.",
    "Same-source two-trait post-result comparison; no general moderator slope or causal mediation.",
    "Donor-standardized MSE and equal-deer residual pair correlation; not genetic variance or formal mixed-model ICC.",
    "Conditional deer resampling ignores donor fitting, spatial and genomic dependence; seeds share source animals.",
    "No raw identifiers, masks, outcomes or matrix exported."))
write_json(out,args[2],pretty=TRUE,auto_unbox=TRUE,digits=16)
cat(toJSON(out,auto_unbox=TRUE,digits=16),"\n")
