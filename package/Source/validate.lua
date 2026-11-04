local root=arg[1]
ordered=function() return function(t) return t end end
for _,name in ipairs({'MacroOperator','InstanceInput','InstanceOutput','GroupInfo','OperatorInfo','CustomTool','Background','Loader','Clip','RectangleMask','Merge','TextPlus','Transform','Input'}) do _G[name]=function(t) return t end end
Point=function(x,y) return {x,y} end
local tests=0
for _,kind in ipairs({'COMPARISON','REFERENCE','DETAIL'}) do
 local path=root..'/Templates/ZBM_'..kind..'_v11.setting'
 local file=assert(io.open(path));local data=file:read('*a');file:close()
 local obj=assert(load('return '..data,path))().Tools['ZBM_'..kind..'_v11'];local nodes=obj.Tools;local count=0
 for name,node in pairs(nodes) do
  count=count+1
  for port,input in pairs(node.Inputs or {}) do
   if input.SourceOp then assert(nodes[input.SourceOp],name..' missing link '..input.SourceOp) end
   if port=='EffectMask' then assert(input.Source=='Mask') end
   if input.Expression then
    local f=assert(load('return '..input.Expression,name..'.'..port))
    for _,fps in ipairs({23.976,24,25,29.97,30,50,59.94,60}) do
     for _,start in ipairs({0,1001}) do
      for _,seconds in ipairs({1,4,30}) do
       comp={RenderStart=start,RenderEnd=start+math.floor(seconds*fps)-1};Controls={NumberIn1=fps}
       for _,offset in ipairs({0,1,.12*fps,.2*fps,.31*fps,.5*fps,seconds*fps-.18*fps,seconds*fps-1}) do
        time=start+math.min(comp.RenderEnd-start,math.max(0,offset));local v=f();tests=tests+1
        if type(v)=='number' then
         assert(v==v and math.abs(v)<math.huge)
         if port=='Alpha1' or port=='Width' then assert(v>=0 and v<=1) end
        else assert(type(v)=='table' and #v==2) end
       end
      end
     end
    end
   end
  end
 end
 for _,input in pairs(obj.Inputs) do assert(nodes[input.SourceOp]) end
 assert(nodes[obj.Outputs.MainOutput1.SourceOp])
 local visited,active={},{}
 local function visit(n)
  assert(not active[n],'Cycle: '..n)
  if visited[n] then return end
  active[n]=true
  for _,inp in pairs(nodes[n].Inputs or {}) do if inp.SourceOp then visit(inp.SourceOp) end end
  active[n]=nil;visited[n]=true
 end
 visit('UI_Position')
 print(kind..': Lua syntax, source links, mask ports, output graph and expressions PASS; '..count..' nodes')
end
print('Expression evaluations: '..tests)
print('Resolve host compatibility and Windows execution remain UNTESTED.')
