#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020)
# Description: Simple plotting script for pico analysis tuples
# Instructions:
#   ./plot_v10.py -y 2018 -c mutau
#   ./plot_v10.py -y 2018 -c config/setup_mutau.yml
#   ./plot_v10.py -y 2018 -c mutau -S baseline -V m_vis
#>>>>IMPORTANT!!
#>>>>Run with --serial option if using py3:
#   ./plot_v10.py -y 2018 -c mutau --serial

# from config.samples_v12 import *
from config.samples_Summer24v15 import *
from TauFW.Plotter.plot.string import filtervars
from TauFW.Plotter.plot.utils import LOG as PLOG
from TauFW.Plotter.plot.Plot import Plot, deletehist
import yaml
import time


def plot(sampleset,setup,parallel=True,tag="",extratext="",outdir="plots",era="",
         varfilter=None,selfilter=None,fraction=False,pdf=False):
  """Test plotting of SampleSet class for data/MC comparison."""
  LOG.header("plot")
  
  channel  = setup["channel"]
  
  if 'baselineCuts' in setup: # baseline pre-selections
    baseline = setup['baselineCuts']
  else:
    raise IOError("No baseline selection for channel %r defined!"%(channel))
  
  selections = [ # plot these selections
    Sel('baseline',baseline)
  ]
  if 'regions' in setup: # add extra regions on top of baseline
    for region in setup['regions']:
      skwargs = setup['regions'][region].copy() # extra key-word options
      assert 'definition' in skwargs
      selstr = setup['baselineCuts']+" && "+skwargs.pop('definition')
      selections.append(Sel(region,selstr,**skwargs))
  selections = filtervars(selections,selfilter) # filter variable list with -S/--sel flag
  
  # VARIABLES
  variables = [
    Var('pt_1',  "Muon pt",    40,  0, 120, ctitle={'etau':"Electron pt",'tautau':"Leading tau_h pt",'mumu':"Leading muon pt",'emu':"Electron pt"},cbins={"nbtag\w*>":(40,0,200)}),
    Var('pt_2',  "tau_h pt",   40,  0, 120, ctitle={'tautau':"Subleading tau_h pt",'mumu':"Subleading muon pt",'emu':"Muon pt"},cbins={"nbtag\w*>":(40,0,200)}),
    Var('eta_1', "Muon eta",   30, -3,   3, ctitle={'etau':"Electron eta",'tautau':"Leading tau_h eta",'mumu':"Leading muon eta",'emu':"Electron eta"},ymargin=1.7,pos='T',ncols=2),
    Var('eta_2', "tau_h eta",  30, -3,   3, ctitle={'etau':"Electron eta",'tautau':"Subleading tau_h eta",'mumu':"Subleading muon eta",'emu':"Muon eta"},ymargin=1.7,pos='T',ncols=2),
    Var('phi_1', "Muon phi",   30, -3,   3, ctitle={'etau':"Electron phi",'tautau':"Leading tau_h phi",'mumu':"Leading muon phi",'emu':"Electron phi"},ymargin=1.7,pos='T',ncols=2),
    Var('phi_2', "tau_h phi",  30, -3,   3, ctitle={'etau':"Electron phi",'tautau':"Subleading tau_h phi",'mumu':"Subleading muon phi",'emu':"Muon phi"},ymargin=1.7,pos='T',ncols=2),
    Var('mt_1',  "mt(mu,MET)", 40,  0, 200, ctitle={'etau':"mt(mu,MET)",'tautau':"mt(tau,MET)",'emu':"mt(e,MET)"},cbins={"nbtag\w*>":(50,0,250)}),
    Var("jpt_1",  29,   10,  300, veto=[r"njets\w*==0"]),
    Var("jpt_2",  29,   10,  300, veto=[r"njets\w*==0"]),
    Var("jeta_1", 53, -5.4,  5.2, ymargin=1.6,pos='T',ncols=2,veto=[r"njets\w*==0"]),
    Var("jeta_2", 53, -5.4,  5.2, ymargin=1.6,pos='T',ncols=2,veto=[r"njets\w*==0"]),
    Var('npv',    40,  0,  80),
    Var('njets',   8,  0,   8),
    Var('nbtag', "Number of b jets (Medium, pt > 30 GeV)", 8, 0, 8),
    Var('met',    50,  0, 150,cbins={"nbtag\w*>":(50,0,250)}),
    #Var('genmet', 50,  0, 150, fname="$VAR_log", logyrange=4, data=False, logy=True, ncols=2, pos='TT'),
    Var('pt_ll',   "p_{T}(mutau_h)", 25, 0, 200, ctitle={'etau':"p_{T}(etau_h)",'tautau':"p_{T}(tau_htau_h)",'emu':"p_{T}(emu)"}),
    Var('dR_ll',   "DR(mutau_h)",    30, 0, 6.0, ctitle={'etau':"DR(etau_h)",'tautau':"DR(tau_htau_h)",'emu':"DR(emu)"}),
    Var('deta_ll', "deta(mutau_h)",  20, 0, 6.0, ctitle={'etau':"deta(etau_h)",'tautau':"deta(tautau)",'emu':"deta(emu)"},logy=True,pos='TRR',cbins={"abs(deta_ll)<":(10,0,3)}), #, ymargin=8, logyrange=2.6
    Var('dzeta',  56, -180, 100, pos='L;y=0.87',units='GeV',cbins={"nbtag\w*>":(35,-220,130)}),
  ]
  if 'tau' in channel: # mutau, etau, tautau
    loadmacro("python/macros/mapDecayModes.C") # for mapRecoDM
    dmlabels  = ["h^{#pm}","h^{#pm}h^{0}","h^{#pm}h^{#mp}h^{#pm}","h^{#pm}h^{#mp}h^{#pm}h^{0}","Other"]
    variables += [
      Var('m_vis',          40,  0, 200, fname="mvis",ctitle={'mumu':"m_mumu",'emu':"m_emu"},logy=False, cbins={"pt_\d>":(50,0,250),"nbtag\w*>":(60,0,300)},cpos={"pt_\d>[1678]0":'LL;y=0.88'}),
      Var('m_vis',  1, 60,  120, fname="$VAR_1bin", veto=["m_vis>200"] ),
      Var('m_vis',          11,  60, 120, fname="mvis_coarse",ctitle={'mumu':"m_mumu",'emu':"m_emu"},logy=False, cbins={"pt_\d>":(25,0,250),"nbtag\w*>":(30,0,300)},cpos={"pt_\d>[1678]0":'LL;y=0.88'}),
      Var("m_2",            30,  0,   3, title="m_tau",veto=["njet","nbtag","dm_2==0"]),
      Var("dm_2",           14,  0,  14, fname="dm_2",title="Reconstructed tau_h decay mode",veto="dm_2==",position="TMC",ymargin=1.2),

      Var("decayModePNet_2", 14,0,14, title="Reconstructed tau_h PNet decay mode"),
      Var("decayModeUParT_2", 14,0,14, title="Reconstruction tau_h UParT decay mode"),

      # Var("rawPNetVSjet_2",  "Score_{PNetVSjet}",50, -0.05, 1.,ymin = 1e3,cbins={"rawPNetVS":(50, 0.75,1.05)},pos='ML', logy=True), #veto=["rawUParTVS","DeepTau2018v2p5"]),
      Var("rawPNetVSjet_2",  "Score_{PNetVSjet}",30, 0, 1.,ymin = 1e3, pos='ML', logy=True), #veto=["rawUParTVS","DeepTau2018v2p5"]),
      Var("rawPNetVSe_2",  "Score_{PNetVSe}",50, -0.05, 1.,ymin = 1e3, logy=True,cbins={"rawPNetVS":(50, 0.3,1.05)},pos='ML'), #veto=["rawUParTVS","DeepTau2018v2p5"]),
      Var("rawPNetVSmu_2",  "Score_{PNetVSmu}",50, -0.05, 1.,ymin = 1e3,cbins={"rawPNetVS":(30, 0.78,1.05)},pos='ML', logy=True), #veto=["rawUParTVS","DeepTau2018v2p5"]),

      Var("rawDeepTau2018v2p5VSjet_2",  "Score_{DeepTau2018v2p5VSjet}",30, 0.94, 1.,ymin = 1e3,pos='ML', logy=True, veto=["rawUParTVS","rawPNetVS"],ymargin=1.3),
      Var("rawDeepTau2018v2p5VSe_2",  "Score_{DeepTau2018v2p5VSe}",30, -0.05, 1.,ymin = 1e3,cbins={"DeepTau2018":(50, 0.2,1.05)}, pos='ML',ncols=3 ,logy=True, veto=["rawUParTVS","rawPNetVS"],ymargin=1.3),
      Var("rawDeepTau2018v2p5VSmu_2",  "Score_{DeepTau2018v2p5VSmu}",30, -0.05, 1.,ymin = 1e3,cbins={"DeepTau2018":(50, 0.8,1.05)},pos='ML', logy=True, veto=["rawUParTVS","rawPNetVS"],ymargin=1.3),

      Var("rawUParTVSe_2",  "Score_{ UParTVSe}",50, -0.05, 1.,ymin = 1e3,cbins={"rawUParTVS":(75, 0.05,1.05)}, logy=True,fname="rawUParTVSe_2_log",pos="L",ncols=2,ymargin=1.3),
      Var("rawUParTVSmu_2",  "Score_{UParTVSmu}",50, -0.05, 1.,ymin = 1e2,cbins={"rawUParTVS":(50, 0.75,1.05)},pos='ML', logy=True,fname="rawUParTVSmu_2_log",ncols=2,ymargin=1.3),
      # Var("rawUParTVSjet_2",  "Score_{UParTVSjet}",50, -0.05, 1.,ymin = 1e3, cbins={"rawUParTVS":(75, 0.25,1.05)},logy=True,fname="rawUParTVSjet_2_log",pos="TR",ncols=2,ymargin=1.3),
      Var("rawUParTVSjet_2",  "Score_{UParTVSjet}",30, 0, 1.,ymin = 1e3,logy=True,fname="rawUParTVSjet_2_log",pos="TR",ncols=2,ymargin=1.3),


      Var("probDM0UParT_2", "Prob of DM_{UParT}=0", 21, 0, 1.05, fname="probDM0UParT_2",logy=True, pos="R",veto=["rawPNetVS","DeepTau2018v2p5"]),
      Var("probDM1UParT_2", "Prob of DM_{UParT}=1", 21, 0, 1.05, fname="probDM1UParT_2",logy=True, pos="R",veto=["rawPNetVS","DeepTau2018v2p5"]),
      Var("probDM2UParT_2", "Prob of DM_{UParT}=2", 21, 0, 1.05, fname="probDM2UParT_2",logy=True, pos="R",veto=["rawPNetVS","DeepTau2018v2p5"]),
      Var("probDM10UParT_2", "Prob of DM_{UParT}=10", 21, 0, 1.05, fname="probDM10UParT_2",logy=True, pos="R",veto=["rawPNetVS","DeepTau2018v2p5"]),
      Var("probDM11UParT_2", "Prob of DM_{UParT}=11", 21, 0, 1.05, fname="probDM11UParT_2",logy=True, pos="R",veto=["rawPNetVS","DeepTau2018v2p5"]),
      Var("decayModeUParT_2", "decayMode_UParT", 14,  0,  14, fname="decayModeUParT_2",title="Reconstructed tau_h UParT decay mode",position="TMC",veto=["rawPNetVS","DeepTau2018v2p5"],ymargin=1.7),

      Var("probDM0PNet_2", "Prob of DM_{PNet}=0", 21, 0, 1.05, fname="probDM0PNet_2",logy=True, pos="R", veto=["rawUParTVS","DeepTau2018v2p5"]),
      Var("probDM1PNet_2", "Prob of DM_{PNet}=1", 21, 0, 1.05, fname="probDM1PNet_2",logy=True, pos="R", veto=["rawUParTVS","DeepTau2018v2p5"]),
      Var("probDM2PNet_2", "Prob of DM_{PNet}=2", 21, 0, 1.05, fname="probDM2PNet_2",logy=True, pos="R", veto=["rawUParTVS","DeepTau2018v2p5"]),
      Var("probDM10PNet_2", "Prob of DM_{PNet}=10", 21, 0, 1.05, fname="probDM10PNet_2",logy=True, pos="R", veto=["rawUParTVS","DeepTau2018v2p5"]),
      Var("probDM11PNet_2", "Prob of DM_{PNet}=11", 21, 0, 1.05, fname="probDM11PNet_2",logy=True, pos="R", veto=["rawUParTVS","DeepTau2018v2p5"]),

      Var("ptCorrUParT_2",  "pt CorrUParT tau",40, 0, 120, fname="ptCorrUParT_2",title="pt CorrUParT tau", pos="L",veto=["rawPNetVS","DeepTau2018v2p5"]),
      Var("qConfUParT_2",  "q CorrUParT tau",4, -2, 2, fname="qConfUParT_2",title="q CorrUParT tau", pos="L",veto=["rawPNetVS","DeepTau2018v2p5"]),
      
    ]
  elif 'mumu' in channel or 'ee' in channel:
    variables += [
      Var('m_ll', "m_mumu", 40,  0,  200, fname="$VAR", cbins={"m_vis>200":(40,200,1000)}), # alias: m_ll alias of m_vis
      Var('m_ll', "m_mumu", 40,  0,  200, fname="$VAR_log", logy=True, ymin=1e2, cbins={"m_vis>200":(40,200,1000)} ),
      # Var('m_ll', "m_mumu", 40, 70,  110, fname="$VAR_Zmass", veto=["m_vis>200"] ),
      # Var('m_ll', "m_mumu",  1, 70,  110, fname="$VAR_1bin", veto=["m_vis>200"] ),
      Var('iso_1', 50, 0.,1., ymin = 1e2,logy=True),
      Var('iso_2', 50, 0.,1., ymin = 1e2,logy=True),
    ]
  variables  = filtervars(variables,varfilter)  # filter variable list with -V/--var flag
  
  # PLOT
  outdir = ensuredir(repkey(outdir,CHANNEL=channel,ERA=era))
  exts   = ['png','pdf','root'] if pdf else ['root'] # extensions
  for selection in selections:
    print(">>> Selection %r: %r"%(selection.title,selection.selection))
    stacks = sampleset.getstack(variables,selection,method='QCD_OSSS',scale=1, parallel=parallel)
    fname  = "%s/$VAR_%s-%s-%s$TAG"%(outdir,channel.replace('mu','m').replace('tau','t'),selection.filename,era)
    text   = "%s: %s"%(channel.replace('mu',"#mu").replace('tau',"#tau_{h}"),selection.title)
    if extratext:
      text += ("" if '\n' in extratext[:3] else ", ") + extratext
    #for stack, variable in stacks.iteritems():
    for stack, variable in stacks.items(): # python 3
      #position = "" #variable.position or 'topright'
      max_yield = max(
          [h.GetMaximum() for h in stack.hists if h] +
          ([stack.datahist.GetMaximum()] if stack.datahist else [])
      )
      stack.ymax = 1.8 * max_yield
      stack.draw(fraction=fraction)
      stack.drawlegend() #position)
      stack.drawtext(text)
      stack.saveas(fname,ext=exts,tag=tag)
      stack.close()

    '''
    #ratio plot between DeepTau 2.1 and 2.5
    for sample in sampleset.expsamples:
      splitsamples = sample.splitsamples
      for splits in splitsamples:
          print("-----------------------------")
          print("TEST")
          print(splits) 
           
          #if "DY" in str(sample):
          #jet
          print("var: ", variables[0].name)
          fname2 = "%s/compareDeepTauVSjet_%s-%s-%s-%s$TAG"%(outdir,channel.replace('mu','m').replace('tau','t'),selection.filename,era,str(splits))
          vars  = [v for v in variables if "rawDeepTau" in v.name and "VSjet" in v.name ]
          names = [v.name.replace('rawDeepTau', '').replace('VSjet_2','') for v in variables if "rawDeepTau" in v.name and "VSjet" in v.name ]  
          hists = splits.gethist(vars,selection,parallel=parallel)
               
          for norm in [True]:
	      #print norm, hists
	      ntag = '_norm' if norm else "_lumi"
	      plot = Plot(hists,norm=norm, xtitle="rawDeepTauVSjet")
	      plot.draw(ratio=True,lstyle=1, logy=True)
	      plot.drawlegend(header=str(splits),entries=names)
	      plot.drawtext(text)
	      plot.saveas(fname2,ext=['png'],tag=ntag) #,'pdf'
	      plot.close(keep=True)
          deletehist(hists)

        
          #mu
          fname2 = "%s/compareDeepTauVSmu_%s-%s-%s-%s$TAG"%(outdir,channel.replace('mu','m').replace('tau','t'),selection.filename,era, str(splits))

          vars  = [v for v in variables if "rawDeepTau" in v.name and "VSmu" in v.name ]
          names = [v.name.replace('rawDeepTau', '').replace('VSmu_2','') for v in variables if "rawDeepTau" in v.name and "VSmu" in v.name ]  
          hists = splits.gethist(vars,selection,parallel=parallel)
        
          for norm in [True]:
              #print norm, hists
              ntag = '_norm' if norm else "_lumi"
              plot = Plot(hists,norm=norm, xtitle="rawDeepTauVSmu")
              plot.draw(ratio=True,lstyle=1, logy=True, ymin = 1e-5)
              plot.drawlegend(header=str(splits),entries=names)
              plot.drawtext(text)
              plot.saveas(fname2,ext=['png'],tag=ntag) #,'pdf'
              plot.close(keep=True)
          deletehist(hists)

     
          #e
          fname2 = "%s/compareDeepTauVSe_%s-%s-%s-%s$TAG"%(outdir,channel.replace('mu','m').replace('tau','t'),selection.filename,era, str(splits))

          vars  = [v for v in variables if "rawDeepTau" in v.name and "VSe" in v.name ]
          names = [v.name.replace('rawDeepTau', '').replace('VSe_2','') for v in variables if "rawDeepTau" in v.name and "VSe" in v.name ]  
          hists = splits.gethist(vars,selection,parallel=parallel)
        
          for norm in [True]:
              #print norm, hists
              ntag = '_norm' if norm else "_lumi"
              plot = Plot(hists,norm=norm, xtitle="rawDeepTauVSe")
              plot.draw(ratio=True,lstyle=1, logy=True)
              plot.drawlegend(header=str(splits),entries=names)
              plot.drawtext(text)
              plot.saveas(fname2,ext=['png'],tag=ntag) #,'pdf'
              plot.close(keep=True)
          deletehist(hists)

      
      if "SingleMuon_Run2018" in str(sample):
        #jet
        print("var: ", variables[0].name)
        fname2 = "%s/compareDeepTauVSjet_%s-%s-%s-%s$TAG"%(outdir,channel.replace('mu','m').replace('tau','t'),selection.filename,era,str(sample))
        vars  = [v for v in variables if "rawDeepTau" in v.name and "VSjet" in v.name ]
        names = [v.name.replace('rawDeepTau', '').replace('VSjet_2','') for v in variables if "rawDeepTau" in v.name and "VSjet" in v.name ]  
        hists = sample.gethist(vars,selection,parallel=parallel)
        
        for norm in [True]:
		  #print norm, hists
		  ntag = '_norm' if norm else "_lumi"
		  plot = Plot(hists,norm=norm, xtitle="rawDeepTauVSjet")
		  plot.draw(ratio=True,lstyle=1, logy=True)
		  plot.drawlegend(header=str(sample),entries=names)
		  plot.drawtext(text)
		  plot.saveas(fname2,ext=['png'],tag=ntag) #,'pdf'
		  plot.close(keep=True)
        deletehist(hists)


        #mu
        fname2 = "%s/compareDeepTauVSmu_%s-%s-%s-%s$TAG"%(outdir,channel.replace('mu','m').replace('tau','t'),selection.filename,era, str(sample))

        vars  = [v for v in variables if "rawDeepTau" in v.name and "VSmu" in v.name ]
        names = [v.name.replace('rawDeepTau', '').replace('VSmu_2','') for v in variables if "rawDeepTau" in v.name and "VSmu" in v.name ]  
        hists = sample.gethist(vars,selection,parallel=parallel)
        
        for norm in [True]:
                  #print norm, hists
                  ntag = '_norm' if norm else "_lumi"
                  plot = Plot(hists,norm=norm, xtitle="rawDeepTauVSmu")
                  plot.draw(ratio=True,lstyle=1, logy=True)
                  plot.drawlegend(header=str(sample),entries=names)
                  plot.drawtext(text)
                  plot.saveas(fname2,ext=['png'],tag=ntag) #,'pdf'
                  plot.close(keep=True)
        deletehist(hists)

     
        #e
        fname2 = "%s/compareDeepTauVSe_%s-%s-%s-%s$TAG"%(outdir,channel.replace('mu','m').replace('tau','t'),selection.filename,era, str(sample))

        vars  = [v for v in variables if "rawDeepTau" in v.name and "VSe" in v.name ]
        names = [v.name.replace('rawDeepTau', '').replace('VSe_2','') for v in variables if "rawDeepTau" in v.name and "VSe" in v.name ]  
        hists = sample.gethist(vars,selection,parallel=parallel)
        
        for norm in [True]:
                  #print norm, hists
                  ntag = '_norm' if norm else "_lumi"
                  plot = Plot(hists,norm=norm, xtitle="rawDeepTauVSe")
                  plot.draw(ratio=True,lstyle=1, logy=True)
                  plot.drawlegend(header=str(sample),entries=names)
                  plot.drawtext(text)
                  plot.saveas(fname2,ext=['png'],tag=ntag) #,'pdf'
                  plot.close(keep=True)
        deletehist(hists)
        '''
  

def main(args):
  configs   = args.configs
  eras      = args.eras
  parallel  = args.parallel
  varfilter = args.varfilter
  selfilter = args.selfilter
  notauidsf = args.notauidsf
  extratext = args.text
  fraction  = args.fraction
  pdf       = args.pdf
  outdir    = "plots/$ERA/$CHANNEL"
  fname     = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  #fname     =  "/nfs/user/pmastra/DeepTau2p5/analysis/$ERA/$CHANNEL/$GROUP/$SAMPLE_$CHANNEL$TAG.root"
   
  # LOOP over configs / channels
  for config in configs:
    if not config.endswith(".yml"): # config = channel name
      config = "config/setup_%s.yml"%(config) # assume this file name pattern
    print(">>> Using configuration file: %s"%config)
    with open(config, 'r') as file:
      setup = yaml.safe_load(file)
    tag = setup.get('tag',"")+args.tag
    
    for era in eras:
      setera(era) # set era for plot style and lumi-xsec normalization
      addsfs = [ ] #"getTauIDSF(dm_2,genmatch_2)"]
      rmsfs  = [ ] if (setup['channel']=='mumu' or not notauidsf) else ['idweight_2','ltfweight_2'] # remove tau ID SFs
      split  = ['DY'] if 'tau' in setup['channel'] else [ ] # split these backgrounds into tau components
      sampleset = getsampleset(setup['channel'],era,fname=fname,rmsf=rmsfs,addsf=addsfs,split=split)
      plot(sampleset,setup,parallel=parallel,tag=tag,extratext=extratext,outdir=outdir,era=era,
           varfilter=varfilter,selfilter=selfilter,fraction=fraction,pdf=pdf)
      #sampleset.close()
  

if __name__ == "__main__":
  from argparse import ArgumentParser, RawTextHelpFormatter
  start = time.time()
  eras = ['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018','2022_preEE','2022_postEE', '2023C', '2023D', '2024', '2025']
  description = """Simple plotting script for pico analysis tuples"""
  parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=eras, default=['2017'],
                                         help="set era" )
  parser.add_argument('-c', '--config', '--channel',
                                         dest='configs', type=str, nargs='+', default=['config/setup_mutau.yml'], action='store',
                                         help="config file(s) containing channel setup for samples and selections, default=%(default)r" )
  parser.add_argument('-V', '--var',     dest='varfilter', nargs='+',
                                         help="only plot the variables passing this filter (glob patterns allowed)" )
  parser.add_argument('-S', '--sel',     dest='selfilter', nargs='+',
                                         help="only plot the selection passing this filter (glob patterns allowed)" )
  parser.add_argument('-s', '--serial',  dest='parallel', action='store_false',
                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-F', '--fraction',dest='fraction', action='store_true',
                                         help="include fraction stack in ratio plot" )
  parser.add_argument('-p', '--pdf',     dest='pdf', action='store_true',
                                         help="create pdf version of each plot" )
  parser.add_argument('-r', '--nosf',    dest='notauidsf', action='store_true',
                                         help="remove DeepTau ID SF" )
  parser.add_argument('-t', '--tag',     default="", help="extra tag for output" )
  parser.add_argument('-T', '--text',    default="", help="extra text on plot" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  end = time.time()
  runtime = end - start

  if runtime < 60:
      print(f'Runtime: {runtime:.2f} seconds')
  elif runtime < 3600:  # Less than one hour
      minutes = runtime / 60
      print(f'Runtime: {minutes:.2f} minutes')
  else:
      hours = runtime / 3600
      print(f'Runtime: {hours:.2f} hours')

  print("\n>>> Done.")
  
