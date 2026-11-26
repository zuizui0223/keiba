# Schema-only audit. Never execute scripts distributed with datasets.
suppressPackageStartupMessages(library(jsonlite))
args <- commandArgs(trailingOnly=TRUE)
stopifnot(length(args)==2)
root <- args[1]
out <- args[2]
objects <- list()
meta <- list()
keys <- list()
matkeys <- list()
clean_names <- function(x) {
  if(is.null(x)) return(character())
  if(length(x)>80) return(paste0("<",length(x)," columns; omitted>"))
  # Do not emit labels that look like individual keys or arbitrary row names.
  if(any(nchar(x)>80)) return(paste0("<",length(x)," long names; omitted>"))
  x
}
safe_id <- function(x) {
  z <- as.character(x)
  ifelse(is.na(z)|!nzchar(trimws(z)),NA_character_,z)
}
inspect <- function(x,source,file,obj) {
  label <- paste(source,file,obj,sep="/")
  d <- dim(x)
  base <- list(source=source,file=file,object=obj,class=class(x),dimensions=as.integer(d),length=length(x))
  if (length(d)==2 && d[1]==d[2] && d[1]>=20 && d[1]<=5000 &&
      (is.matrix(x)||inherits(x,"Matrix")||is.data.frame(x))) {
    a <- as.matrix(x)
    if(is.numeric(a)) {
      rn <- rownames(a); cn <- colnames(a)
      labels <- !is.null(rn)&&!is.null(cn)&&!anyNA(rn)&&!anyNA(cn)&&
        !any(!nzchar(rn))&&!any(!nzchar(cn))&&!anyDuplicated(rn)&&!anyDuplicated(cn)
      same_set <- labels&&setequal(rn,cn)
      base$matrix_check <- list(n=nrow(a),finite=all(is.finite(a)),labels_unique=labels,
        row_column_same_set=same_set,row_column_same_order=labels&&identical(rn,cn))
      if(same_set&&all(is.finite(a))) {
        a <- a[,match(rn,cn),drop=FALSE]
        base$matrix_check$max_abs_asymmetry <- max(abs(a-t(a)))
        if(nrow(a)<=1000&&base$matrix_check$max_abs_asymmetry<1e-7) {
          ev <- eigen((a+t(a))/2,symmetric=TRUE,only.values=TRUE)$values
          base$matrix_check$min_eigenvalue <- min(ev)
        }
        matkeys[[label]] <<- list(source=source,file=file,object=obj,ids=rn)
      }
      meta[[label]] <<- base
      return(invisible(NULL))
    }
  }
  if(is.data.frame(x)||is.matrix(x)) {
    x <- as.data.frame(x)
    nms <- names(x)
    base$columns <- clean_names(nms)
    # Candidate detection is not an accepted semantic mapping.
    idcols <- grep("(^id$|(^|[_.])id($|[_.])|(^|[_.])(animal|deer|ind|individual|chevreuil|identifiant|ident|animalid|idanimal)([_.]|$))",nms,ignore.case=TRUE,value=TRUE)
    yearcols <- grep("(^|[_.])(year|annee|yr)([_.]|$)",nms,ignore.case=TRUE,value=TRUE)
    monthcols <- grep("(^|[_.])(month|mois|mon)([_.]|$)",nms,ignore.case=TRUE,value=TRUE)
    datecols <- grep("(date|yearmonth|year_month|datetime|timestamp|period|session|time|month|mois|year|annee)",nms,ignore.case=TRUE,value=TRUE)
    base$column_classes <- if(length(nms)<=80) lapply(x,class) else NULL
    base$identifier_candidates <- idcols
    base$time_candidates <- datecols
    times <- list()
    for(k in datecols) {
      v <- x[[k]]
      s <- as.character(v)
      # YYYY-MM, YYYY-MM-DD or ISO timestamp (not merely month-of-year).
      iso <- !is.na(s)&grepl("^(19|20)[0-9]{2}[-/](0[1-9]|1[0-2])($|[-/ ][0-9]{2})",s)
      yearonly <- !is.na(s)&grepl("^(19|20)[0-9]{2}$",s)
      if(inherits(v,c("Date","POSIXct","POSIXlt"))) s <- format(v,"%Y-%m-%d")
      if(sum(!is.na(s))>0 && (inherits(v,c("Date","POSIXct","POSIXlt"))||all(iso[!is.na(s)]))) times[[k]] <- list(value=s,kind="calendar_date_or_month")
      else if(sum(!is.na(s))>0&&all(yearonly[!is.na(s)])) times[[k]] <- list(value=s,kind="calendar_year")
    }
    for(y in yearcols) for(m in monthcols) {
      yy <- suppressWarnings(as.integer(as.character(x[[y]])))
      mm <- suppressWarnings(as.integer(as.character(x[[m]])))
      ok <- !is.na(yy)&yy>=1900&yy<=2100&!is.na(mm)&mm>=1&mm<=12
      if(sum(ok)>0)times[[paste(y,m,sep="+")]] <- list(value=ifelse(ok,sprintf("%04d-%02d",yy,mm),NA_character_),kind="year_month_candidate")
    }
    results <- list()
    for(k in idcols) {
      id <- safe_id(x[[k]])
      ids <- unique(id[!is.na(id)])
      keys[[paste(label,k,sep="/")]] <<- list(source=source,file=file,object=obj,column=k,ids=ids)
      t <- list(candidate=k,nonmissing=sum(!is.na(id)),unique_ids=length(ids),repeated_ids=sum(table(id)>1),max_records=if(length(ids))max(table(id))else 0L,dated=list())
      for(n in names(times)) {
        v <- times[[n]]$value;ok <- !is.na(id)&!is.na(v)
        byid <- split(v[ok],id[ok])
        reps <- vapply(byid,function(a)length(unique(a)),integer(1))
        t$dated[[n]] <- list(kind=times[[n]]$kind,valid_rows=sum(ok),
          distinct_periods=length(unique(v[ok])),individuals_with_periods=length(reps),
          individuals_ge2_periods=sum(reps>=2),individuals_ge3_periods=sum(reps>=3))
      }
      results[[k]] <- t
    }
    base$candidate_key_support <- results
  }
  meta[[label]] <<- base
}
if(dir.exists(root))for(source in list.dirs(root,full.names=FALSE,recursive=FALSE)) {
  for(f in list.files(file.path(root,source),full.names=TRUE)) {
    ext <- tolower(tools::file_ext(f));name <- basename(f)
    tryCatch({
      if(ext=="csv") inspect(read.csv(f,check.names=FALSE,stringsAsFactors=FALSE),source,name,"csv")
      if(ext %in% c("rdata","rda")) {
        # Load into an isolated environment, do not call saved functions.
        env <- new.env(parent=emptyenv())
        n <- load(f,envir=env)
        for(k in n) {
          x <- get(k,envir=env,inherits=FALSE)
          inspect(x,source,name,k)
          # One level of named container objects, no script evaluation.
          if(is.list(x)&&!is.data.frame(x)&&length(x)<=30&&!is.null(names(x)))
            for(j in seq_along(x))if(is.data.frame(x[[j]])||is.matrix(x[[j]])||inherits(x[[j]],"Matrix"))inspect(x[[j]],source,name,paste(k,names(x)[j],sep="/"))
        }
      }
    },error=function(e)meta[[paste(source,name,"error",sep="/")]] <<- list(source=source,file=name,status="HOLD_PARSE_ERROR",error_class=class(e)[1]))
  }
}
joins <- list()
for(a in keys)for(b in matkeys) {
  common <- intersect(a$ids,b$ids)
  joins[[length(joins)+1L]] <- list(table_source=a$source,table_file=a$file,object=a$object,id_candidate=a$column,
    matrix_source=b$source,matrix_file=b$file,matrix_object=b$object,table_unique_ids=length(a$ids),
    matrix_n=length(b$ids),exact_string_overlap=length(common),table_ids_all_in_matrix=length(a$ids)>0&&all(a$ids%in%b$ids))
}
cross <- list()
for(a in keys)for(b in keys)if(a$source=="gervais2020"&&b$source=="gervais2022"){
  cross[[length(cross)+1L]]<-list(table2020=a$file,key2020=a$column,table2022=b$file,key2022=b$column,
    unique2020=length(a$ids),unique2022=length(b$ids),exact_string_overlap=length(intersect(a$ids,b$ids)))
}
res<-list(status=if(length(meta))"SCHEMA_AND_CANDIDATE_SUPPORT_ONLY" else "HOLD_NO_ACQUIRED_DATA",
          objects=unname(meta),table_matrix_candidate_joins=joins,cross_release_candidate_overlap=cross,
          caveats=c("Column names are candidates only; verify README semantics before analysis.","Calendar candidates not verified observation chronology.","Exact string overlap is not verified identity across releases.","No outcome values, animal IDs, raw files, or genetic effect exported."))
write_json(res,out,pretty=TRUE,auto_unbox=TRUE,na="null")
cat(toJSON(res,auto_unbox=TRUE,na="null"),"\n")
